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
ML_RESULTS_FILE = "results/ml_model_comparison.csv"
ML_PREDICTIONS_FILE = "results/ml_cost_predictions.csv"

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

    ml_results_df = pd.read_csv(
        ML_RESULTS_FILE
    )

    ml_predictions_df = pd.read_csv(
        ML_PREDICTIONS_FILE
    )

    return (
        cost_df,
        recommendation_df,
        underutilization_df,
        ml_results_df,
        ml_predictions_df
    )


(
    df,
    recommendation_df,
    underutilization_df,
    ml_results_df,
    ml_predictions_df
) = load_data()

# ============================================================
# TITLE
# ============================================================

st.title("☁️ Cloud Cost Optimization Analytics")

st.markdown(
    "### Big Data Analytics Platform for Cloud Cost Monitoring "
    "and Optimization"
)

st.caption(
    "Hadoop HDFS • MapReduce • Python • Pandas • Streamlit • Machine Learning"
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
# Filters
# ------------------------------------------------------------

high_cost_only = st.sidebar.checkbox(
    "Show High-Cost Records Only"
)

high_priority_only = st.sidebar.checkbox(
    "Show High-Priority Recommendations Only"
)

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
# Provider filter
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
# Service filter
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
# High-cost filter
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
# High-priority filter
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
# Underutilization filter
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
# TOP UNDERUTILIZATION OPPORTUNITIES
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
            f"Score "
            f"{row['Underutilization_Score']:.2f}"
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
# CROSS-CLOUD PROVIDER OPTIMIZATION
# ============================================================

st.subheader(
    "☁️ Cross-Cloud Provider Optimization"
)

PROVIDER_RECOMMENDATION_FILE = (
    "results/provider_recommendations.csv"
)

# ------------------------------------------------------------
# Load provider recommendations
# ------------------------------------------------------------

@st.cache_data
def load_provider_recommendations():

    return pd.read_csv(
        PROVIDER_RECOMMENDATION_FILE
    )


provider_df = load_provider_recommendations()

# ------------------------------------------------------------
# Apply dashboard filters
# ------------------------------------------------------------

filtered_provider_df = provider_df.copy()

# Cloud provider filter
if selected_provider != "All":

    filtered_provider_df = (
        filtered_provider_df[
            filtered_provider_df[
                "Current_Provider"
            ]
            ==
            selected_provider
        ]
    )

# Service filter
if selected_service != "All":

    filtered_provider_df = (
        filtered_provider_df[
            filtered_provider_df[
                "Current_Service"
            ]
            ==
            selected_service
        ]
    )

# ------------------------------------------------------------
# Migration candidates
# ------------------------------------------------------------

migration_candidates = (
    filtered_provider_df[
        (
            filtered_provider_df[
                "Recommended_Provider"
            ]
            !=
            filtered_provider_df[
                "Current_Provider"
            ]
        )
        &
        (
            filtered_provider_df[
                "Estimated_Monthly_Savings"
            ]
            > 0
        )
    ]
    .copy()
)

# ------------------------------------------------------------
# KPIs
# ------------------------------------------------------------

provider_candidate_count = (
    len(migration_candidates)
)

provider_monthly_savings = (
    migration_candidates[
        "Estimated_Monthly_Savings"
    ].sum()
)

provider_annual_savings = (
    provider_monthly_savings * 12
)

high_confidence_count = (
    migration_candidates[
        "Recommendation_Confidence"
    ]
    == "HIGH"
).sum()

pcol1, pcol2, pcol3, pcol4 = st.columns(4)

pcol1.metric(
    "Migration Candidates",
    f"{provider_candidate_count:,}"
)

pcol2.metric(
    "Potential Monthly Savings",
    f"${provider_monthly_savings:,.2f}"
)

pcol3.metric(
    "Potential Annual Savings",
    f"${provider_annual_savings:,.2f}"
)

pcol4.metric(
    "High Confidence",
    f"{high_confidence_count:,}"
)

st.caption(
    "Savings are estimated from observed cost-per-hour "
    "benchmarks for equivalent services across AWS, "
    "Azure, and GCP. They are not guaranteed savings."
)

# ------------------------------------------------------------
# Recommended provider distribution
# ------------------------------------------------------------

if not migration_candidates.empty:

    st.subheader(
        "🔄 Recommended Provider Distribution"
    )

    provider_distribution = (
        migration_candidates[
            "Recommended_Provider"
        ]
        .value_counts()
    )

    fig, ax = plt.subplots(
        figsize=(9, 4)
    )

    provider_distribution.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        "Recommended Cloud Provider Distribution"
    )

    ax.set_xlabel(
        "Recommended Provider"
    )

    ax.set_ylabel(
        "Number of Migration Candidates"
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
        "No provider migration opportunities "
        "match the selected filters."
    )

# ------------------------------------------------------------
# Top migration opportunities
# ------------------------------------------------------------

st.subheader(
    "🎯 Top Cross-Cloud Migration Opportunities"
)

top_provider_candidates = (
    migration_candidates
    .sort_values(
        "Estimated_Monthly_Savings",
        ascending=False
    )
    .head(10)
)

if not top_provider_candidates.empty:

    provider_display_columns = [

        "Account_ID",

        "Current_Provider",

        "Current_Service",

        "Service_Category",

        "Region",

        "Usage_Hours",

        "Current_Monthly_Cost",

        "Current_Cost_Per_Hour",

        "Recommended_Provider",

        "Alternative_Cost_Per_Hour",

        "Estimated_Alternative_Cost",

        "Estimated_Monthly_Savings",

        "Estimated_Savings_Percentage",

        "Recommendation_Confidence"
    ]

    available_provider_columns = [

        column
        for column in provider_display_columns
        if column in top_provider_candidates.columns
    ]

    st.dataframe(
        top_provider_candidates[
            available_provider_columns
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No migration candidates available "
        "for the current filters."
    )

# ------------------------------------------------------------
# Detailed recommendations
# ------------------------------------------------------------

if not top_provider_candidates.empty:

    st.subheader(
        "💡 Provider Recommendation Details"
    )

    for _, row in top_provider_candidates.iterrows():

        with st.expander(
            f"{row['Account_ID']} | "
            f"{row['Current_Provider']} "
            f"→ "
            f"{row['Recommended_Provider']} | "
            f"{row['Current_Service']} | "
            f"${row['Estimated_Monthly_Savings']:,.2f} "
            "potential monthly savings"
        ):

            dcol1, dcol2, dcol3 = st.columns(3)

            dcol1.write(
                f"**Current Provider:** "
                f"{row['Current_Provider']}"
            )

            dcol2.write(
                f"**Recommended Provider:** "
                f"{row['Recommended_Provider']}"
            )

            dcol3.write(
                f"**Service Category:** "
                f"{row['Service_Category']}"
            )

            dcol1.write(
                f"**Current Cost:** "
                f"${row['Current_Monthly_Cost']:,.2f}"
            )

            dcol2.write(
                f"**Estimated Alternative:** "
                f"${row['Estimated_Alternative_Cost']:,.2f}"
            )

            dcol3.write(
                f"**Potential Savings:** "
                f"${row['Estimated_Monthly_Savings']:,.2f}"
            )

            st.write(
                f"**Savings Percentage:** "
                f"{row['Estimated_Savings_Percentage']:.2f}%"
            )

            st.write(
                f"**Confidence:** "
                f"{row['Recommendation_Confidence']}"
            )

            st.write(
                f"**Recommendation:** "
                f"{row['Recommendation']}"
            )

            st.caption(
                "Provider recommendations are based on "
                "observed benchmark costs for equivalent "
                "service categories. Actual migration "
                "costs and architecture requirements "
                "should be evaluated separately."
            )

st.divider()
# ============================================================
# MACHINE LEARNING COST PREDICTION
# ============================================================

st.subheader(
    "🔮 Machine Learning Cost Prediction"
)

# ------------------------------------------------------------
# Best model
# ------------------------------------------------------------

best_model_row = (
    ml_results_df
    .sort_values(
        "MAE"
    )
    .iloc[0]
)

best_model_name = (
    best_model_row["Model"]
)

best_mae = (
    best_model_row["MAE"]
)

best_rmse = (
    best_model_row["RMSE"]
)

best_r2 = (
    best_model_row["R2_Score"]
)

mlcol1, mlcol2, mlcol3, mlcol4 = st.columns(4)

mlcol1.metric(
    "Best Model",
    best_model_name
)

mlcol2.metric(
    "MAE",
    f"${best_mae:.2f}"
)

mlcol3.metric(
    "RMSE",
    f"${best_rmse:.2f}"
)

mlcol4.metric(
    "R² Score",
    f"{best_r2:.4f}"
)

st.caption(
    "The model was selected using the lowest Mean Absolute Error "
    "on the held-out test dataset."
)

# ============================================================
# MODEL COMPARISON
# ============================================================

st.subheader(
    "📈 ML Model Comparison"
)

st.dataframe(
    ml_results_df.sort_values(
        "MAE"
    ),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

st.subheader(
    "🎯 Actual vs Predicted Cloud Cost"
)

# ------------------------------------------------------------
# Apply dashboard filters to ML predictions
# ------------------------------------------------------------

filtered_ml_predictions = ml_predictions_df.copy()

# Provider filter
if selected_provider != "All":

    filtered_ml_predictions = (
        filtered_ml_predictions[
            filtered_ml_predictions["Cloud_Provider"]
            == selected_provider
        ]
    )

# Service filter
if selected_service != "All":

    filtered_ml_predictions = (
        filtered_ml_predictions[
            filtered_ml_predictions["Service"]
            == selected_service
        ]
    )

# ------------------------------------------------------------
# Display filtered graph
# ------------------------------------------------------------

if filtered_ml_predictions.empty:

    st.warning(
        "⚠️ No ML test-set predictions are available "
        "for the selected provider/service combination."
    )

else:

    plot_df = (
        filtered_ml_predictions
        .reset_index(drop=True)
        .copy()
    )

    plot_df["Record"] = range(
        1,
        len(plot_df) + 1
    )

    fig, ax = plt.subplots(
        figsize=(12, 5)
    )

    ax.plot(
        plot_df["Record"],
        plot_df["Actual_Monthly_Cost"],
        label="Actual Cost"
    )

    ax.plot(
        plot_df["Record"],
        plot_df["Predicted_Monthly_Cost"],
        label="Predicted Cost"
    )

    # Dynamic title
    provider_text = (
        selected_provider
        if selected_provider != "All"
        else "All Providers"
    )

    service_text = (
        selected_service
        if selected_service != "All"
        else "All Services"
    )

    ax.set_title(
        "Actual vs Predicted Monthly Cost\n"
        f"{provider_text} | {service_text}"
    )

    ax.set_xlabel(
        "Test Record"
    )

    ax.set_ylabel(
        "Monthly Cost ($)"
    )

    ax.legend()

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

    st.caption(
        f"Showing {len(plot_df)} ML test records "
        f"for the selected filters."
    )

# ============================================================
# ML PREDICTION TABLE
# ============================================================

st.subheader(
    "🔬 ML Prediction Results"
)

ml_display_columns = [
    "Cloud_Provider",
    "Service",
    "Region",
    "Usage_Hours",
    "Data_Transfer_GB",
    "Storage_GB",
    "Actual_Monthly_Cost",
    "Predicted_Monthly_Cost",
    "Absolute_Error",
    "Best_Model"
]

available_ml_columns = [
    column
    for column in ml_display_columns
    if column in ml_predictions_df.columns
]

st.dataframe(
    ml_predictions_df[
        available_ml_columns
    ],
    use_container_width=True,
    hide_index=True
)

st.info(
    "The current ML component evaluates cloud-cost prediction "
    "performance on a held-out test set. An R² score of 0.3613 "
    "indicates moderate predictive capability; it should not be "
    "interpreted as a guaranteed future-cost forecast."
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
        • Machine Learning Cost Prediction
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
        service-specific optimization recommendations, detects
        potential underutilization, and evaluates machine-learning
        models for cloud-cost prediction.

        Hadoop HDFS and MapReduce provide the Big Data processing
        foundation, while Python, Pandas, scikit-learn, and
        Streamlit provide analytics, machine learning, and
        interactive visualization.
        """
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Cloud Cost Optimization Analytics | "
    "Hadoop HDFS + MapReduce + Python + ML + Streamlit"
)