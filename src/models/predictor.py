import pickle
import numpy as np
import pandas as pd

class RainfallPredictor:
    def __init__(self, model_path="model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self._load_model()

    def _load_model(self):
        try:
            with open(self.model_path, "rb") as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                self.feature_cols = data['features']
        except FileNotFoundError:
            print(f"Model file {self.model_path} not found.")

    def predict(self, input_features):
        """Predicts rainfall for a given set of features."""
        if not self.model or not self.scaler:
            return None
            
        # Ensure input_features is a DataFrame with correct column order
        if isinstance(input_features, list):
            input_features = pd.DataFrame([input_features], columns=self.feature_cols)
            
        input_scaled = self.scaler.transform(input_features)
        return self.model.predict(input_scaled)[0]
