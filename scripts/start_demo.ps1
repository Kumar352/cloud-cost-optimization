[CmdletBinding()]
param([switch]$SkipTests, [switch]$SkipMapReduce, [int]$DashboardPort = 8503)

$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$java = "C:\Java\jdk17"
$hadoop = "$env:USERPROFILE\OneDrive\Desktop\BigData\hadoop-3.2.2"
if (-not (Test-Path "$java\bin\java.exe")) {
    Write-Host "JDK 17 not found at $java" -ForegroundColor Red
    exit 2
}
if (-not (Test-Path "$hadoop\bin\hadoop.cmd")) {
    Write-Host "Hadoop not found at $hadoop. Update the hadoop path in scripts/start_demo.ps1." -ForegroundColor Red
    exit 2
}
$env:JAVA_HOME = $java
$env:HADOOP_HOME = $hadoop
$env:HADOOP_CONF_DIR = "$hadoop\etc\hadoop"
$env:PATH = "$java\bin;$hadoop\bin;$hadoop\sbin;$env:PATH"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logs = Join-Path $env:TEMP "cloud-cost-optimization-demo-logs"
New-Item -ItemType Directory -Path $logs -Force | Out-Null

function Step([string]$s) { Write-Host ""; Write-Host "=== $s ===" -ForegroundColor Cyan }
function HProc([string]$pattern) {
    @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^java(w)?\.exe$' -and $_.CommandLine -match $pattern })
}
function Listening([int]$port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
}

Step "1/6: Java and Hadoop versions"
& "$java\bin\java.exe" -version
& "$hadoop\bin\hadoop.cmd" version
if ($LASTEXITCODE -ne 0) { Write-Host "Hadoop version command failed; continue only to collect diagnostics." -ForegroundColor Yellow }

Step "2/6: Python dependencies and tests"
$check = "import streamlit, pandas, plotly, sklearn, boto3, pyarrow; print('Required Python modules found')"
& python -c $check
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Python requirements..." -ForegroundColor Yellow
    & python -m pip install -r (Join-Path $repo "requirements.txt")
}
if (-not $SkipTests) {
    & python -m compileall -q src tests
    if ($LASTEXITCODE -ne 0) { Write-Host "Python compilation failed." -ForegroundColor Red }
    & python -m pytest -q tests/test_project_data.py
    if ($LASTEXITCODE -eq 0) { Write-Host "Project tests passed." -ForegroundColor Green }
    else { Write-Host "Tests failed; frontend will still be attempted." -ForegroundColor Yellow }
}

Step "3/6: Start and verify HDFS (never format NameNode)"
$nnPattern = "org\.apache\.hadoop\.hdfs\.server\.namenode\.NameNode"
$dnPattern = "org\.apache\.hadoop\.hdfs\.server\.datanode\.DataNode"
$rmPattern = "org\.apache\.hadoop\.yarn\.server\.resourcemanager\.ResourceManager"
$nmPattern = "org\.apache\.hadoop\.yarn\.server\.nodemanager\.NodeManager"
if ((HProc $nnPattern).Count -eq 0 -or (HProc $dnPattern).Count -eq 0) {
    Write-Host "Starting HDFS..." -ForegroundColor Yellow
    & "$hadoop\sbin\start-dfs.cmd"
}
for ($i=0; $i -lt 15; $i++) {
    if ((HProc $nnPattern).Count -gt 0 -and (HProc $dnPattern).Count -gt 0) { break }
    Start-Sleep -Seconds 2
}
$hdfsOk = ((HProc $nnPattern).Count -gt 0 -and (HProc $dnPattern).Count -gt 0)
if ($hdfsOk) {
    & "$hadoop\bin\hdfs.cmd" dfs -ls /
    if ($LASTEXITCODE -eq 0) { Write-Host "HDFS responded to an HDFS CLI request." -ForegroundColor Green }
    else { $hdfsOk = $false; Write-Host "HDFS process exists but HDFS CLI failed." -ForegroundColor Yellow }
} else {
    Write-Host "HDFS did not become healthy. No HDFS metadata was formatted or deleted." -ForegroundColor Yellow
}

Step "4/6: Start and verify YARN"
if (-not (Listening 8032) -or (HProc $rmPattern).Count -eq 0 -or (HProc $nmPattern).Count -eq 0) {
    Write-Host "Starting YARN..." -ForegroundColor Yellow
    & "$hadoop\sbin\start-yarn.cmd"
}
for ($i=0; $i -lt 15; $i++) {
    if ((Listening 8032) -and (HProc $rmPattern).Count -gt 0 -and (HProc $nmPattern).Count -gt 0) { break }
    Start-Sleep -Seconds 2
}
$yarnOk = ((Listening 8032) -and (HProc $rmPattern).Count -gt 0 -and (HProc $nmPattern).Count -gt 0)
if ($yarnOk) {
    Write-Host "YARN ResourceManager and NodeManager appear healthy; port 8032 is listening." -ForegroundColor Green
} else {
    Write-Host "YARN still failed its health check; do not submit a job that could hang." -ForegroundColor Yellow
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^java(w)?\.exe$' -and $_.CommandLine -match 'hadoop|yarn' } |
        Select-Object ProcessId, Name, CommandLine | Format-List
    Get-ChildItem "$hadoop\logs" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'yarn|resourcemanager|nodemanager' } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 5 FullName, LastWriteTime, Length | Format-Table -AutoSize
}

Step "5/6: Run a fresh MapReduce job only if HDFS and YARN are healthy"
$mrOk = $false
if ($SkipMapReduce) {
    Write-Host "MapReduce skipped by parameter." -ForegroundColor Yellow
} elseif (-not $hdfsOk -or -not $yarnOk) {
    Write-Host "MapReduce skipped because HDFS/YARN is unhealthy." -ForegroundColor Yellow
} else {
    $dataset = Join-Path $repo "data\raw\cloud_cost_data.csv"
    $jar = Join-Path $repo "hadoop\cloud-cost-analysis.jar"
    if (-not (Test-Path $dataset) -or -not (Test-Path $jar)) {
        Write-Host "Dataset or hadoop\cloud-cost-analysis.jar missing; MapReduce skipped." -ForegroundColor Yellow
    } else {
        $inputDir = "/cloud_cost_project/demo-input"
        $inputPath = "$inputDir/cloud_cost_data_$stamp.csv"
        $outputPath = "/cloud_cost_project/processed/demo_output_$stamp"
        & "$hadoop\bin\hdfs.cmd" dfs -mkdir -p $inputDir
        & "$hadoop\bin\hdfs.cmd" dfs -put $dataset $inputPath
        if ($LASTEXITCODE -eq 0) {
            $outLog = Join-Path $logs "mapreduce-$stamp.out.log"
            $errLog = Join-Path $logs "mapreduce-$stamp.err.log"
            $hadoopCmd = "$hadoop\bin\hadoop.cmd"
            $line = '"' + $hadoopCmd + '" jar "' + $jar + '" CloudCostDriver "' + $inputPath + '" "' + $outputPath + '"'
            $job = Start-Process -FilePath "$env:WINDIR\System32\cmd.exe" -ArgumentList @("/d", "/c", $line) -WorkingDirectory $repo -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
            if (-not $job.WaitForExit(180000)) {
                Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue
                Write-Host "MapReduce exceeded 180 seconds; wrapper stopped to avoid an indefinite wait." -ForegroundColor Yellow
                Write-Host "Logs: $outLog and $errLog"
            } else {
                $job.Refresh()
                if (Test-Path $outLog) { Get-Content $outLog -Tail 25 }
                if (Test-Path $errLog) { Get-Content $errLog -Tail 35 }
                if ($job.ExitCode -eq 0) {
                    & "$hadoop\bin\hdfs.cmd" dfs -cat "$outputPath/part-r-00000"
                    if ($LASTEXITCODE -eq 0) {
                        $mrOk = $true
                        Write-Host "Fresh MapReduce output verified at $outputPath" -ForegroundColor Green
                    }
                } else {
                    Write-Host "MapReduce exited with code $($job.ExitCode)." -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "Failed to upload the demo input to HDFS." -ForegroundColor Yellow
        }
    }
}

Step "6/6: Launch frontend and open browser"
try {
    $accountId = (& aws sts get-caller-identity --query Account --output text 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $accountId -eq "473009223309") {
        $env:CLOUD_COST_AWS_CUR_BUCKET = "cloud-cost-optimization-$accountId"
        $env:CLOUD_COST_AWS_CUR_PREFIX = "raw/aws-cur/cloud-cost-optimization-cur/data/"
        $env:CLOUD_COST_AWS_REGION = "us-east-1"
        Write-Host "AWS identity verified for the project account." -ForegroundColor Green
    } else {
        Write-Host "AWS identity not verified. Frontend will still run; use Synthetic cross-cloud demo if live CUR access fails." -ForegroundColor Yellow
    }
} catch {
    Write-Host "AWS CLI identity check unavailable; frontend will still run." -ForegroundColor Yellow
}

$port = $DashboardPort
while ((Listening $port) -and $port -lt ($DashboardPort + 10)) { $port++ }
if (Listening $port) {
    Write-Host "Ports $DashboardPort through $port are occupied. Stop the old Streamlit process and rerun." -ForegroundColor Red
    exit 3
}
$python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $python) { Write-Host "Python not found." -ForegroundColor Red; exit 4 }
$dashOut = Join-Path $logs "streamlit-$port.out.log"
$dashErr = Join-Path $logs "streamlit-$port.err.log"
$dashPath = Join-Path $repo "src\dashboard.py"
$app = Start-Process -FilePath $python -ArgumentList @("-m","streamlit","run",$dashPath,"--server.port","$port") -WorkingDirectory $repo -RedirectStandardOutput $dashOut -RedirectStandardError $dashErr -PassThru
$ready = $false
for ($i=0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if (Listening $port) { $ready = $true; break }
    $app.Refresh()
    if ($app.HasExited) { break }
}
if ($ready) {
    $url = "http://localhost:$port"
    Write-Host "Frontend is listening at $url (PID $($app.Id)). Opening browser." -ForegroundColor Green
    Start-Process $url
} else {
    Write-Host "Frontend failed to start. Output: $dashOut ; errors: $dashErr" -ForegroundColor Red
    if (Test-Path $dashOut) { Get-Content $dashOut -Tail 40 }
    if (Test-Path $dashErr) { Get-Content $dashErr -Tail 60 }
    exit 5
}
Write-Host ""
Write-Host "DEMO STATUS" -ForegroundColor Cyan
Write-Host "HDFS healthy:       $hdfsOk"
Write-Host "YARN healthy:       $yarnOk"
Write-Host "Fresh MR succeeded: $mrOk"
Write-Host "Frontend URL:       http://localhost:$port"
Write-Host "Logs:               $logs"
Write-Host "The AI chatbot still requires AWS to authorize the chosen Bedrock model."
