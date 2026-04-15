import sys
import os
import pickle
import json

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.data.data_loader import load_and_merge_data, get_subdivision_data
from src.data.feature_engineering import apply_feature_engineering
from src.models.trainer import ModelTrainer, visualize_performance
from src.utils.logger import setup_logger
from src.config import (
    HISTORICAL_DATA_PATH, EXTENDED_DATA_PATH, PLOTS_DIR, METRICS_PATH, MODEL_PATH
)

logger = setup_logger("Trainer")

def run_training_pipeline():
    logger.info("Starting Modular ML Pipeline...")
    
    # 2. Data Loading
    df_full, df_extended = load_and_merge_data(HISTORICAL_DATA_PATH, EXTENDED_DATA_PATH)
    subdivisions = df_full['SUBDIVISION'].unique()
    
    trainer = ModelTrainer(random_state=42)
    best_overall_model = None
    best_overall_scaler = None
    lowest_overall_rmse = float('inf')
    feature_cols = None
    all_metrics = {}

    # 3. Main Processing Loop
    for sub in subdivisions:
        logger.info(f"Processing Subdivision: {sub}")
        
        # Data filtering and melting
        df_melted = get_subdivision_data(df_full, sub, df_extended)
        
        # Feature engineering
        df_featured = apply_feature_engineering(df_melted, sub)
        
        if feature_cols is None:
            feature_cols = ['Year', 'Month', 'Season', 'Lag_1', 'Rolling_Avg_3', 'Lat', 'Lon', 'Is_Coastal', 'Elevation']
            
        X = df_featured[feature_cols]
        y = df_featured['Avg_Rainfall']
        
        if len(X) < 30:
            logger.warning(f"Skipping {sub}: Insufficient data.")
            continue

        # Train and compare
        best_model, scaler, results, X_test_scaled, y_test = trainer.train_and_compare(X, y)
        
        # Find local best for comparison/visualization
        local_best_rmse = min([r['RMSE'] for r in results])
        logger.info(f"Best Local RMSE for {sub}: {local_best_rmse:.4f}")
        all_metrics[sub.upper()] = round(local_best_rmse, 2)
        
        # Save visualization
        visualize_performance(best_model, X_test_scaled, y_test, sub, save_dir=PLOTS_DIR)
        
        # Update global best for representative region
        if sub in ["VIDARBHA", "GETYOURWEATHER"]:
            best_overall_model = best_model
            best_overall_scaler = scaler
            lowest_overall_rmse = local_best_rmse

    # 4. Save Final Model Artifacts
    if best_overall_model:
        model_to_save = {
            'model': best_overall_model,
            'scaler': best_overall_scaler,
            'features': feature_cols
        }
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model_to_save, f)
        logger.info(f"Best model and scaler saved to {MODEL_PATH} (RMSE: {lowest_overall_rmse:.4f})")

    # 5. Save all metrics to JSON for UI
    with open(METRICS_PATH, "w") as f:
        json.dump(all_metrics, f)
    logger.info(f"Subdivision metrics saved to {METRICS_PATH}")

    logger.info("MODULAR PIPELINE COMPLETE")

if __name__ == "__main__":
    run_training_pipeline()
