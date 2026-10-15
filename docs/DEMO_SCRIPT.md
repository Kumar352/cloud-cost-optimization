# Demo Script — Cloud Cost Optimization Analytics Using Hadoop

Suggested duration: 5–7 minutes. Use this as a walkthrough, not a claim that every component is currently running end to end.

## 1. Problem and objective (30 seconds)

“Cloud environments generate large usage and billing datasets. This project demonstrates how to summarize cloud costs, surface unusually expensive records, recommend resources for review, forecast costs, and present insights in a dashboard.”

## 2. Architecture and data sources (45 seconds)

Open `README.md` and `docs/ARCHITECTURE.md`.

“The project has two distinct data tracks. The repository’s AWS/Azure/GCP-shaped CSV is synthetic demo data used for reproducible cross-cloud analytics. Separately, the AWS infrastructure configures CUR 2.0 billing export to S3 and scheduled Lambda workload telemetry. Those sources should not be combined into real cross-cloud billing totals unless an explicit normalization and integration step has been run.”

## 3. Python analytics (60 seconds)

Show `src/cloud_cost_analysis.py` and `data/processed/cloud_cost_analysis.csv`.

“The analysis derives cost per hour, uses a 90th-percentile cost threshold to flag high-cost records, and assigns service-specific review suggestions. The flags are triage signals, not proof of waste.”

Optionally demonstrate a reproducible run from the repository root:

```powershell
python -m pip install -r requirements.txt
python src/cloud_cost_analysis.py
```

## 4. Hadoop MapReduce (60 seconds)

Show `hadoop/CloudCostDriver.java`, `hadoop/CloudCostMapper.java`, `hadoop/CloudCostReducer.java`, and `hadoop/cloud-cost-analysis.jar`.

Explain that the Java implementation emits grouped cost summaries for provider, service, and region. If you run a new job, show the completed YARN application state and the actual HDFS output directory. **Do not describe a stored CSV or JAR alone as proof that a new MapReduce run succeeded.**

If ResourceManager is unavailable during the demo, state that the local YARN startup is currently a blocker, then show the implementation and existing result artifacts without claiming a current successful run.

## 5. Dashboard and recommendations (90 seconds)

Start from the project root:

```powershell
streamlit run src/dashboard.py
```

Show the executive summary, provider/service/region views, anomaly analysis, underutilization, FinOps recommendations, and cost prediction sections that load successfully.

“The dashboard is a decision-support view. Recommendations are proposed actions for engineers to review; estimated savings are scenarios and not realized savings.”

## 6. AWS and Terraform (60–90 seconds)

Show selected files under `terraform/`, then show live console evidence only for resources and data that you have personally verified.

“Terraform declares the AWS environment. The configured CUR export delivers AWS billing data to S3 in Parquet format. The scheduled Lambda workload writes separate JSON telemetry to S3. CUR delivery has a delay, so the export’s refresh metadata and billing period matter.”

Do not expose AWS account identifiers, database endpoints, secret values, billing records containing identifiers, Terraform state, or credentials on screen.

## 7. Validation and limitations (30 seconds)

Show the green [Python project checks](https://github.com/Kumar352/cloud-cost-optimization/actions/workflows/python-checks.yml) workflow and `docs/SUBMISSION_CHECKLIST.md`.

“Automated checks compile the Python modules and run smoke tests against the dataset, analysis function, and Hadoop output parser. The checks do not prove that the AWS and Hadoop pipelines have all been executed end to end today.”

## Questions to be ready for

- **Are the cross-cloud results real billing data?** No. The committed cross-cloud CSV is synthetic. Real AWS CUR Parquet is a separate AWS-only source.
- **Are savings guaranteed?** No. Savings are estimates based on heuristics and assumptions; an organization would need to validate feasibility and actual post-change costs.
- **Did the Hadoop job run during the demo?** Answer from the current YARN application status and logs. If not verified, say so and show code/artifacts instead.
- **How can the project be improved?** Implement and validate a Glue/Athena catalog/query flow for CUR, normalize real provider billing semantics, add temporal holdout evaluation for forecasts, and run the Hadoop pipeline in a stable Linux or managed Hadoop environment.
