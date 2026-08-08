import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# CLOUD COST OPTIMIZATION ANALYTICS DASHBOARD
# ============================================================

st.set_page_config(
    page_title="Cloud Cost Optimization Analytics",
    page_icon="☁️",
    layout="wide"
)

# ============================================================
# FILE PATHS
# ============================================================

DATA_FILE = "data/processed/cloud_cost_analysis.csv"
RECOMMENDATION_FILE = "results/optimization_candidates.csv"
UNDERUTILIZATION_FILE = "results/underutilized_resources.csv"

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    cost_df = pd.read_csv(DATA_FILE)

    recommendation_df = pd.read_csv(
        RECOMMENDATION_FILE
    )

    underutilization_df = pd.read_csv(
        UNDERUTILIZATION_FILE
    )

    return (
        cost_df,
        recommendation_df,
        underutilization_df
    )


df, recommendation_df, underutilization_df = load_data()

# ============================================================
# TITLE
# ============================================================

st.title("☁️ Cloud Cost Optimization Analytics")

st.markdown(
    "### Big Data Analytics Platform for Cloud Cost Monitoring "
    "and Optimization"
)

st.caption(
    "Hadoop HDFS • MapReduce • Python • Pandas • Streamlit"
)

st.divider()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Analysis Filters")

# ------------------------------------------------------------
# Cloud Provider
# ------------------------------------------------------------

providers = ["All"] + sorted(
    df["Cloud_Provider"]
    .dropna()
    .unique()
    .tolist()
)

selected_provider = st.sidebar.selectbox(
    "Cloud Provider",
    providers
)

# ------------------------------------------------------------
# Dynamic Service Filter
# ------------------------------------------------------------

if selected_provider == "All":

    available_services = sorted(
        df["Service"]
        .dropna()
        .unique()
        .tolist()
    )

else:

    available_services = sorted(
        df.loc[
            df["Cloud_Provider"]
            == selected_provider,
            "Service"
        ]
        .dropna()
        .unique()
        .tolist()
    )

services = ["All"] + available_services

selected_service = st.sidebar.selectbox(
    "Cloud Service",
    services
)

# ------------------------------------------------------------
# High Cost Filter
# ------------------------------------------------------------

high_cost_only = st.sidebar.checkbox(
    "Show High-Cost Records Only"
)

# ------------------------------------------------------------
# High Priority Filter
# ------------------------------------------------------------

high_priority_only = st.sidebar.checkbox(
    "Show High-Priority Recommendations Only"
)

# ------------------------------------------------------------
# Underutilization Filter
# ------------------------------------------------------------

underutilized_only = st.sidebar.checkbox(
    "Show Underutilized Resources Only"
)

# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()

filtered_recommendations = recommendation_df.copy()

filtered_underutilization = underutilization_df.copy()

# ------------------------------------------------------------
# Provider
# ------------------------------------------------------------

if selected_provider != "All":

    filtered_df = filtered_df[
        filtered_df["Cloud_Provider"]
        == selected_provider
    ]

    filtered_recommendations = (
        filtered_recommendations[
            filtered_recommendations["Cloud_Provider"]
            == selected_provider
        ]
    )

    filtered_underutilization = (
        filtered_underutilization[
            filtered_underutilization["Cloud_Provider"]
            == selected_provider
        ]
    )

# ------------------------------------------------------------
# Service
# ------------------------------------------------------------

if selected_service != "All":

    filtered_df = filtered_df[
        filtered_df["Service"]
        == selected_service
    ]

    filtered_recommendations = (
        filtered_recommendations[
            filtered_recommendations["Service"]
            == selected_service
        ]
    )

    filtered_underutilization = (
        filtered_underutilization[
            filtered_underutilization["Service"]
            == selected_service
        ]
    )

# ------------------------------------------------------------
# High Cost
# ------------------------------------------------------------

if high_cost_only:

    filtered_df = filtered_df[
        filtered_df["Optimization_Flag"]
        == "High Cost"
    ]

    filtered_recommendations = (
        filtered_recommendations[
            filtered_recommendations["Optimization_Flag"]
            == "High Cost"
        ]
    )

# ------------------------------------------------------------
# High Priority
# ------------------------------------------------------------

if high_priority_only:

    filtered_recommendations = (
        filtered_recommendations[
            filtered_recommendations[
                "Optimization_Priority"
            ]
            == "HIGH"
        ]
    )

# ------------------------------------------------------------
# Underutilization
# ------------------------------------------------------------

if underutilized_only:

    filtered_underutilization = (
        filtered_underutilization[
            filtered_underutilization[
                "Underutilization_Flag"
            ]
            == "YES"
        ]
    )

# ============================================================
# EMPTY DATA CHECK
# ============================================================

if filtered_df.empty:

    st.warning(
        "⚠️ No cost data is available for the selected filters."
    )

    st.info(
        "Try selecting 'All' for Cloud Provider or Cloud Service."
    )

    st.stop()

# ============================================================
# KPI CALCULATIONS
# ============================================================

total_cost = (
    filtered_df["Monthly_Cost"].sum()
)

average_cost = (
    filtered_df["Monthly_Cost"].mean()
)

record_count = len(filtered_df)

high_cost_count = (
    filtered_df["Optimization_Flag"]
    == "High Cost"
).sum()

high_cost_spending = filtered_df.loc[
    filtered_df["Optimization_Flag"]
    == "High Cost",
    "Monthly_Cost"
].sum()

potential_savings = (
    high_cost_spending * 0.15
)

# ============================================================
# COST OVERVIEW
# ============================================================

st.subheader("📊 Cost Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Monthly Cost",
    f"${total_cost:,.2f}"
)

col2.metric(
    "Records",
    f"{record_count:,}"
)

col3.metric(
    "Average Cost / Record",
    f"${average_cost:,.2f}"
)

col4.metric(
    "High-Cost Records",
    f"{high_cost_count:,}"
)

st.divider()

# ============================================================
# PROVIDER ANALYSIS
# ============================================================

st.subheader("☁️ Cost by Cloud Provider")

provider_cost = (
    filtered_df
    .groupby("Cloud_Provider")["Monthly_Cost"]
    .sum()
    .sort_values(ascending=False)
)

if not provider_cost.empty:

    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    provider_cost.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        "Total Cost by Cloud Provider"
    )

    ax.set_xlabel(
        "Cloud Provider"
    )

    ax.set_ylabel(
        "Monthly Cost ($)"
    )

    ax.tick_params(
        axis="x",
        rotation=0
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

else:

    st.info(
        "No provider data available."
    )

st.divider()

# ============================================================
# SERVICE ANALYSIS
# ============================================================

st.subheader("🛠️ Cost by Cloud Service")

service_cost = (
    filtered_df
    .groupby("Service")["Monthly_Cost"]
    .sum()
    .sort_values(ascending=False)
)

if not service_cost.empty:

    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    service_cost.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        "Total Cost by Cloud Service"
    )

    ax.set_xlabel(
        "Cloud Service"
    )

    ax.set_ylabel(
        "Monthly Cost ($)"
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

else:

    st.info(
        "No service data available."
    )

st.divider()

# ============================================================
# REGION ANALYSIS
# ============================================================

st.subheader("🌎 Cost by Region")

region_cost = (
    filtered_df
    .groupby("Region")["Monthly_Cost"]
    .sum()
    .sort_values(ascending=False)
)

if not region_cost.empty:

    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    region_cost.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        "Total Cost by Region"
    )

    ax.set_xlabel(
        "Region"
    )

    ax.set_ylabel(
        "Monthly Cost ($)"
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

else:

    st.info(
        "No regional data available."
    )

st.divider()

# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

st.subheader("🤖 Recommendation Engine")

priority_counts = (
    filtered_recommendations[
        "Optimization_Priority"
    ]
    .value_counts()
)

rcol1, rcol2, rcol3 = st.columns(3)

rcol1.metric(
    "🔴 High Priority",
    int(
        priority_counts.get(
            "HIGH",
            0
        )
    )
)

rcol2.metric(
    "🟠 Medium Priority",
    int(
        priority_counts.get(
            "MEDIUM",
            0
        )
    )
)

rcol3.metric(
    "🟢 Low Priority",
    int(
        priority_counts.get(
            "LOW",
            0
        )
    )
)

st.divider()

# ============================================================
# OPTIMIZATION CENTER
# ============================================================

st.subheader("🚨 Optimization Center")

optimization_candidates = (
    filtered_recommendations[
        filtered_recommendations[
            "Optimization_Flag"
        ]
        == "High Cost"
    ]
    .sort_values(
        "Monthly_Cost",
        ascending=False
    )
)

if not optimization_candidates.empty:

    st.write(
        f"**{len(optimization_candidates)} "
        "high-cost resources identified "
        "for optimization review.**"
    )

    display_columns = [
        "Account_ID",
        "Cloud_Provider",
        "Service",
        "Region",
        "Usage_Hours",
        "Monthly_Cost",
        "Recommendation",
        "Optimization_Priority",
        "Recommended_Action",
        "Optimization_Score"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in optimization_candidates.columns
    ]

    st.dataframe(
        optimization_candidates[
            available_columns
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No high-cost resources found "
        "for the current filters."
    )

st.divider()

# ============================================================
# TOP OPTIMIZATION OPPORTUNITIES
# ============================================================

st.subheader(
    "🎯 Top Optimization Opportunities"
)

top_candidates = (
    filtered_recommendations
    .sort_values(
        "Optimization_Score",
        ascending=False
    )
    .head(10)
)

if not top_candidates.empty:

    for _, row in top_candidates.iterrows():

        with st.expander(
            f"{row['Account_ID']} | "
            f"{row['Cloud_Provider']} | "
            f"{row['Service']} | "
            f"${row['Monthly_Cost']:,.2f}"
        ):

            info1, info2, info3 = st.columns(3)

            info1.write(
                f"**Region:** {row['Region']}"
            )

            info2.write(
                f"**Priority:** "
                f"{row['Optimization_Priority']}"
            )

            info3.write(
                f"**Score:** "
                f"{row['Optimization_Score']:.2f}/100"
            )

            st.write(
                f"**Recommendation:** "
                f"{row['Recommendation']}"
            )

            st.write(
                f"**Recommended Action:** "
                f"{row['Recommended_Action']}"
            )

else:

    st.info(
        "No optimization opportunities "
        "match the current filters."
    )

st.divider()

# ============================================================
# UNDERUTILIZATION ANALYSIS
# ============================================================

st.subheader(
    "⚠️ Underutilization Analysis"
)

high_underutilized = (
    filtered_underutilization[
        filtered_underutilization[
            "Underutilization_Priority"
        ]
        == "HIGH"
    ]
)

medium_underutilized = (
    filtered_underutilization[
        filtered_underutilization[
            "Underutilization_Priority"
        ]
        == "MEDIUM"
    ]
)

underutilized_candidates = (
    filtered_underutilization[
        filtered_underutilization[
            "Underutilization_Flag"
        ]
        == "YES"
    ]
)

underutilized_spending = (
    underutilized_candidates[
        "Monthly_Cost"
    ].sum()
)

underutilized_savings = (
    underutilized_spending * 0.20
)

ucol1, ucol2, ucol3, ucol4 = st.columns(4)

ucol1.metric(
    "🔴 High",
    len(high_underutilized)
)

ucol2.metric(
    "🟠 Medium",
    len(medium_underutilized)
)

ucol3.metric(
    "⚠️ Candidates",
    len(underutilized_candidates)
)

ucol4.metric(
    "Potential Savings",
    f"${underutilized_savings:,.2f}"
)

st.caption(
    "Potential savings shown here are a 20% scenario "
    "based on candidate spending, not guaranteed savings."
)

# ============================================================
# UNDERUTILIZATION TABLE
# ============================================================

if not underutilized_candidates.empty:

    st.write(
        f"**{len(underutilized_candidates)} "
        "resources show potential underutilization signals.**"
    )

    underutilized_display = [
        "Account_ID",
        "Cloud_Provider",
        "Service",
        "Region",
        "Usage_Hours",
        "Monthly_Cost",
        "Cost_Per_Hour",
        "Underutilization_Priority",
        "Underutilization_Score",
        "Underutilization_Action"
    ]

    available_underutilized_columns = [
        column
        for column in underutilized_display
        if column in underutilized_candidates.columns
    ]

    st.dataframe(
        underutilized_candidates[
            available_underutilized_columns
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No underutilization candidates "
        "match the current filters."
    )

st.divider()

# ============================================================
# UNDERUTILIZATION TOP OPPORTUNITIES
# ============================================================

st.subheader(
    "🔍 Top Underutilization Opportunities"
)

top_underutilized = (
    filtered_underutilization
    .sort_values(
        "Underutilization_Score",
        ascending=False
    )
    .head(10)
)

if not top_underutilized.empty:

    for _, row in top_underutilized.iterrows():

        with st.expander(
            f"{row['Account_ID']} | "
            f"{row['Cloud_Provider']} | "
            f"{row['Service']} | "
            f"Score {row['Underutilization_Score']:.2f}"
        ):

            u1, u2, u3 = st.columns(3)

            u1.write(
                f"**Usage:** "
                f"{row['Usage_Hours']} hours"
            )

            u2.write(
                f"**Monthly Cost:** "
                f"${row['Monthly_Cost']:,.2f}"
            )

            u3.write(
                f"**Cost / Hour:** "
                f"${row['Cost_Per_Hour']:.4f}"
            )

            st.write(
                f"**Priority:** "
                f"{row['Underutilization_Priority']}"
            )

            st.write(
                f"**Underutilization Score:** "
                f"{row['Underutilization_Score']:.2f}/100"
            )

            st.write(
                f"**Recommended Action:** "
                f"{row['Underutilization_Action']}"
            )

st.divider()

# ============================================================
# SAVINGS OPPORTUNITY
# ============================================================

st.subheader(
    "💰 Savings Opportunity"
)

scol1, scol2, scol3 = st.columns(3)

scol1.metric(
    "High-Cost Spending",
    f"${high_cost_spending:,.2f}"
)

scol2.metric(
    "Optimization Scenario",
    "15%"
)

scol3.metric(
    "Potential Monthly Savings",
    f"${potential_savings:,.2f}"
)

st.info(
    "The 15% cost-optimization figure is an analytical "
    "scenario assumption, not a guaranteed saving."
)

st.divider()

# ============================================================
# PROJECT ARCHITECTURE
# ============================================================

with st.expander(
    "🏗️ Project Architecture"
):

    st.markdown(
        """
        **Data Layer**

        Cloud Cost Dataset
        ↓

        **Big Data Processing**

        Hadoop HDFS + MapReduce
        ↓

        **Analytics Layer**

        Python + Pandas
        ↓

        **Optimization Engines**

        Cost Analysis
        • Recommendation Engine
        • Underutilization Detection
        ↓

        **Visualization Layer**

        Streamlit Interactive Dashboard
        """
    )

# ============================================================
# ABOUT PROJECT
# ============================================================

with st.expander(
    "ℹ️ About This Project"
):

    st.write(
        """
        This project analyzes cloud infrastructure usage and
        cost data across AWS, Azure, and GCP.

        The system identifies high-cost resources, generates
        service-specific optimization recommendations, and
        detects potential underutilization using usage,
        monthly cost, and cost-per-hour indicators.

        Hadoop HDFS and MapReduce provide the Big Data processing
        foundation, while Python, Pandas, and Streamlit provide
        analytics and interactive visualization.
        """
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Cloud Cost Optimization Analytics | "
    "Hadoop HDFS + MapReduce + Python + Streamlit"
)