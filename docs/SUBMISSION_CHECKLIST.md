# Submission Checklist — Cloud Cost Optimization Analytics Using Hadoop

Use this checklist to prepare a truthful, reproducible submission.

## Demonstration order

1. Open the repository and explain the objective and architecture.
2. Identify which inputs are synthetic cross-cloud demo records and which artifacts come from AWS CUR 2.0.
3. Show the existing provider/service/region summaries in `results/`.
4. Show anomaly, underutilization, recommendation, and forecast outputs.
5. Launch `streamlit run src/dashboard.py` and walk through working views.
6. Explain the Java Mapper, Reducer, and Driver and show the existing JAR.
7. If a fresh MapReduce run is verified, show YARN application status and output. Otherwise describe the CSV/JAR as repository artifacts and do not claim a successful current run.
8. Show Terraform files and explain key AWS resources and security choices.
9. Show AWS evidence for CUR export, S3 objects, scheduled Lambda telemetry, and RDS only as relevant.
10. Finish with limitations, next steps, and potential (not guaranteed) savings.

## Final local checks

From repository root:

```powershell
python --version
python -m compileall src
git status --short
git log -1 --oneline
```

Run the dashboard in a separate terminal:

```powershell
streamlit run src/dashboard.py
```

In `terraform/`, when Terraform is installed and initialized:

```powershell
terraform fmt -check -recursive
terraform validate
terraform plan
```

Do not apply changes during final packaging unless the plan is understood and intended.

## Evidence to capture

- Repository home page and final commit
- Dashboard overview with readable axes/labels
- Provider, service, region, anomalies, recommendations, and forecast views
- Hadoop source code and (if verified) a completed YARN job
- Terraform validation output and reviewed plan
- AWS CUR export status and an S3 CUR Parquet object (mask account identifiers)
- Lambda schedule and a sample JSON output object
- CloudWatch log evidence of scheduled invocations, with identifiers redacted
- Short README/architecture overview

Do not include passwords, access keys, database secrets, private state files, or unredacted account/customer billing data in screenshots.

## Claims policy

Only report measurements reproducible from the cited input and run. A synthetic-data savings estimate is a scenario, not realized savings. A stored CSV/JAR is not proof of a current job execution. A configured component is not proof that its end-to-end data path is currently working. Separate completed, partially completed, and planned components.

## Operational cautions

- Do not format existing HDFS NameNode metadata.
- Do not delete HDFS metadata directories to troubleshoot YARN.
- Do not submit repeated MapReduce jobs while ResourceManager port 8032 is unavailable.
- Do not destroy/recreate AWS infrastructure just to refresh a demo.
- Keep Terraform state, `.tfvars` secrets, credentials, and database passwords out of Git.
- Check AWS costs for RDS and other always-on resources before leaving them running.
