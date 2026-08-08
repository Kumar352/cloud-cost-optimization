import pandas as pd
import numpy as np
import os

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ============================================================
# CLOUD COST OPTIMIZATION
# MACHINE LEARNING MODEL COMPARISON ENGINE
# ============================================================

INPUT_FILE = "data/raw/cloud_cost_data.csv"
PREDICTION_OUTPUT = "results/ml_cost_predictions.csv"
MODEL_RESULTS_OUTPUT = "results/ml_model_comparison.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    return pd.read_csv(INPUT_FILE)


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):

    features = [
        "Cloud_Provider",
        "Service",
        "Region",
        "Usage_Hours",
        "Data_Transfer_GB",
        "Storage_GB"
    ]

    target = "Monthly_Cost"

    X = df[features].copy()
    y = df[target].copy()

    return X, y


# ============================================================
# PREPROCESSOR
# ============================================================

def create_preprocessor():

    categorical_features = [
        "Cloud_Provider",
        "Service",
        "Region"
    ]

    numerical_features = [
        "Usage_Hours",
        "Data_Transfer_GB",
        "Storage_GB"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                categorical_features
            ),
            (
                "numerical",
                "passthrough",
                numerical_features
            )
        ]
    )

    return preprocessor


# ============================================================
# CREATE MODELS
# ============================================================

def create_models():

    models = {

        "Linear Regression":
            LinearRegression(),

        "Random Forest":
            RandomForestRegressor(
                n_estimators=200,
                random_state=42,
                max_depth=12,
                min_samples_split=4,
                n_jobs=-1
            ),

        "Gradient Boosting":
            GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=3,
                random_state=42
            ),

        "Extra Trees":
            ExtraTreesRegressor(
                n_estimators=200,
                random_state=42,
                max_depth=12,
                min_samples_split=4,
                n_jobs=-1
            )
    }

    return models


# ============================================================
# EVALUATE MODEL
# ============================================================

def evaluate_model(
    model,
    X_train,
    X_test,
    y_train,
    y_test
):

    preprocessor = create_preprocessor()

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )

    # Train
    pipeline.fit(
        X_train,
        y_train
    )

    # Predict
    predictions = pipeline.predict(
        X_test
    )

    # Metrics
    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    return (
        pipeline,
        predictions,
        mae,
        rmse,
        r2
    )


# ============================================================
# MAIN ML PIPELINE
# ============================================================

def run_ml_comparison():

    print("=" * 70)
    print("CLOUD COST MACHINE LEARNING MODEL COMPARISON")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_data()

    print(
        f"Records loaded: {len(df)}"
    )

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    X, y = prepare_data(df)

    print(
        f"Features used: {X.shape[1]}"
    )

    print(
        "Target variable: Monthly_Cost"
    )

    # --------------------------------------------------------
    # Train / Test
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42
        )
    )

    print(
        f"Training records: {len(X_train)}"
    )

    print(
        f"Testing records: {len(X_test)}"
    )

    # --------------------------------------------------------
    # Create models
    # --------------------------------------------------------

    models = create_models()

    results = []

    best_model = None
    best_predictions = None
    best_model_name = None
    best_mae = float("inf")

    # --------------------------------------------------------
    # Evaluate models
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)

    for model_name, model in models.items():

        print()
        print(
            f"Training {model_name}..."
        )

        (
            pipeline,
            predictions,
            mae,
            rmse,
            r2
        ) = evaluate_model(
            model,
            X_train,
            X_test,
            y_train,
            y_test
        )

        results.append({
            "Model": model_name,
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2_Score": round(r2, 4)
        })

        print(
            f"MAE: ${mae:.2f}"
        )

        print(
            f"RMSE: ${rmse:.2f}"
        )

        print(
            f"R²: {r2:.4f}"
        )

        # ----------------------------------------------------
        # Select best model by MAE
        # ----------------------------------------------------

        if mae < best_mae:

            best_mae = mae
            best_model = pipeline
            best_predictions = predictions
            best_model_name = model_name

    # ========================================================
    # SAVE MODEL COMPARISON
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    results_df = results_df.sort_values(
        "MAE"
    )

    os.makedirs(
        "results",
        exist_ok=True
    )

    results_df.to_csv(
        MODEL_RESULTS_OUTPUT,
        index=False
    )

    # ========================================================
    # SAVE BEST MODEL PREDICTIONS
    # ========================================================

    prediction_results = X_test.copy()

    prediction_results["Actual_Monthly_Cost"] = (
        y_test.values
    )

    prediction_results["Predicted_Monthly_Cost"] = (
        best_predictions
    )

    prediction_results["Prediction_Error"] = (
        prediction_results["Actual_Monthly_Cost"]
        -
        prediction_results["Predicted_Monthly_Cost"]
    )

    prediction_results["Absolute_Error"] = (
        prediction_results["Prediction_Error"]
        .abs()
    )

    prediction_results["Best_Model"] = (
        best_model_name
    )

    prediction_results = prediction_results.sort_values(
        "Actual_Monthly_Cost",
        ascending=False
    )

    prediction_results.to_csv(
        PREDICTION_OUTPUT,
        index=False
    )

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    best_row = results_df.iloc[0]

    print()
    print("=" * 70)
    print("BEST MODEL")
    print("=" * 70)

    print(
        f"Selected Model: "
        f"{best_row['Model']}"
    )

    print(
        f"MAE: "
        f"${best_row['MAE']:.2f}"
    )

    print(
        f"RMSE: "
        f"${best_row['RMSE']:.2f}"
    )

    print(
        f"R² Score: "
        f"{best_row['R2_Score']:.4f}"
    )

    print()
    print(
        "Model comparison saved to:"
    )

    print(
        MODEL_RESULTS_OUTPUT
    )

    print()
    print(
        "Best-model predictions saved to:"
    )

    print(
        PREDICTION_OUTPUT
    )

    print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_ml_comparison()