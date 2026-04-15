import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

def evaluate_model(name, model, X_test, y_test):
    """Calculates MAE, RMSE, and R2 Score for a given model."""
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    return {"MAE": mae, "RMSE": rmse, "R2": r2}

def visualize_performance(model, X_test, y_test, subdivision_name, save_dir="static/plots"):
    """Generates and saves Actual vs Predicted and Residual plots for a specific subdivision."""
    predictions = model.predict(X_test)
    residuals = y_test - predictions
    
    os.makedirs(save_dir, exist_ok=True)
    safe_name = subdivision_name.replace(" & ", "_").replace(" ", "_").upper()
    save_path = os.path.join(save_dir, f"{safe_name}.png")
    
    plt.figure(figsize=(15, 6))
    plt.suptitle(f"Model Performance: {subdivision_name}", fontsize=16)
    
    plt.subplot(1, 2, 1)
    plt.scatter(y_test, predictions, alpha=0.6, color='blue', edgecolors='white')
    min_val = min(y_test.min(), predictions.min())
    max_val = max(y_test.max(), predictions.max())
    plt.plot([min_val, max_val], [min_val, max_val], '--r', linewidth=2)
    plt.xlabel('Actual Rainfall (mm)')
    plt.ylabel('Predicted Rainfall (mm)')
    plt.title('Actual vs. Predicted')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.subplot(1, 2, 2)
    plt.scatter(predictions, residuals, alpha=0.6, color='green', edgecolors='white')
    plt.axhline(y=0, color='red', linestyle='--', linewidth=2)
    plt.xlabel('Predicted Rainfall (mm)')
    plt.ylabel('Residuals (Errors)')
    plt.title('Residual Plot')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(save_path)
    plt.close()
    return save_path

class ModelTrainer:
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model_factories = {
            "Linear Regression": lambda: LinearRegression(),
            "Random Forest": lambda: RandomForestRegressor(n_estimators=100, random_state=self.random_state),
            "Gradient Boosting": lambda: GradientBoostingRegressor(n_estimators=100, random_state=self.random_state),
            "XGBoost": lambda: XGBRegressor(n_estimators=100, random_state=self.random_state)
        }

    def train_and_compare(self, X, y):
        """Trains multiple models and returns the best one based on RMSE."""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        best_model = None
        lowest_rmse = float('inf')
        results = []

        for name, factory in self.model_factories.items():
            m = factory()
            m.fit(X_train_scaled, y_train)
            metrics = evaluate_model(name, m, X_test_scaled, y_test)
            results.append({"Model": name, "RMSE": metrics["RMSE"]})
            
            if metrics["RMSE"] < lowest_rmse:
                lowest_rmse = metrics["RMSE"]
                best_model = m
                
        return best_model, scaler, results, X_test_scaled, y_test
