# Architecture Notes

## Logical components

| Component | Role | Evidence for presentation |
|---|---|---|
| Synthetic cross-cloud CSV | Demonstration input for AWS/Azure/GCP-shaped records | `data/raw/cloud_cost_data.csv` and README disclosure |
| HDFS | Hadoop file-system layer | HDFS health checks and file listing |
| Java MapReduce | Groups and aggregates costs | Mapper, Reducer, Driver source, JAR, completed YARN logs if available |
| Python analytics | Anomalies, recommendations, underutilization and prediction workflows | Scripts under `src/` and output files under `results/` |
| Streamlit dashboard | Presents analysis results | Dashboard running locally and screenshots |
| AWS CUR 2.0 export | Ingests AWS billing data to S3 in Parquet | Export status/refresh metadata and S3 objects |
| Lambda + EventBridge | Generates scheduled workload telemetry to S3 | Schedule state, Lambda logs and sample JSON |
| RDS PostgreSQL | Relational storage target for data integration | DB/schema query evidence, with secrets and endpoints redacted |
| Terraform | Declares AWS infrastructure | `terraform/` source plus fmt/validate/plan evidence |

## Data boundaries

Synthetic cross-cloud data is suitable for illustrating analytical logic and comparing provider-like dimensions. It must not be mixed into real billing totals. AWS CUR contains AWS billing line items and must be processed with its own schema, time window, currency, and billing semantics.

## Verification status

Treat this document as a logical architecture description, not an assertion that every edge is currently tested end to end. Mark a component end-to-end verified only when reproducible output or runtime evidence from the current state is available.

## Live CUR analysis and Cost Copilot

The Streamlit app defaults to the live AWS CUR 2.0 data source. It downloads the most recent billing-period Parquet partitions from the project S3 data lake, keeps currencies separate, and computes period/service/daily summaries and IQR high-cost review candidates.

- **CUR Cost Copilot:** deterministic, data-grounded Q&A is the default. Optional Amazon Bedrock mode is disabled unless selected and provided a model ID. It receives summarized billing context rather than raw records. This is grounding/RAG-style context, not LLM fine-tuning.
- **Trainable anomaly model:** the user can train a scikit-learn Isolation Forest over the loaded CUR rows. Training is performed in memory per currency, and scored rows can be downloaded. It does not upload data or persist a model file.
- **Glue/Athena:** terraform/cur_analytics.tf declares a Glue database and manually triggered crawler plus a dedicated Athena workgroup. These resources are not live until reviewed and applied through Terraform; deployment and a successful crawler/query need separate evidence.

