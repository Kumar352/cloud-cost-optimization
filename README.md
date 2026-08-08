\# Cloud Cost Optimization Analytics Using Hadoop



\## Project Overview



Cloud Cost Optimization Analytics is a Big Data project that analyzes cloud usage and cost data to identify high-cost resources and potential cost optimization opportunities.



The project uses Hadoop MapReduce for distributed processing and Python/Pandas for data analysis and visualization.



\## Objectives



\- Analyze cloud usage and monthly costs

\- Compare costs across AWS, Azure, and GCP

\- Identify expensive cloud services and accounts

\- Detect high-cost usage records

\- Generate service-based optimization recommendations

\- Estimate potential cost savings



\## Technologies Used



\- Apache Hadoop 3.2.2

\- HDFS

\- Hadoop MapReduce

\- Java

\- Python

\- Pandas

\- Matplotlib

\- Jupyter Notebook

\- Git/GitHub



\## Dataset



The project analyzes 500 cloud usage records containing:



\- Account ID

\- Cloud Provider

\- Service

\- Region

\- Usage Date

\- Usage Hours

\- Data Transfer

\- Storage

\- Monthly Cost



\## Key Results



| Metric | Result |

|---|---:|

| Records Analyzed | 500 |

| Total Monthly Cloud Cost | $79,395.61 |

| Average Cost per Record | $158.79 |

| High-Cost Records | 50 |

| High-Cost Spending | $15,077.99 |

| Potential Monthly Savings | $2,261.70 |

| Potential Annual Savings | $27,140.38 |



\## Major Findings



\- GCP has the highest total cloud cost.

\- Azure has the highest average cost per record.

\- Azure SQL has the highest total service cost.

\- Virtual Machines have the highest average service cost.

\- `us-west1` has the highest regional cost.

\- The top 10% of records are automatically flagged for optimization review.



\## Optimization Recommendations



High-cost resources are categorized into:



\- Review Compute Usage

\- Review Storage Usage

\- Review Database Usage

\- Review Service Usage



The project uses a 90th-percentile cost threshold to identify high-cost records.



A 15% savings scenario is used to estimate potential savings. This is an analytical assumption and not a guaranteed saving.



\## Project Structure



```text

cloud-cost-optimization/

│

├── data/

│   ├── raw/

│   └── processed/

│

├── notebooks/

│

├── results/

│   ├── optimization\_candidates.csv

│   └── cost\_summary.csv

│

├── src/

│   ├── generate\_dataset.py

│   └── cloud\_cost\_analysis.py

│

├── docs/

│

└── README.md

