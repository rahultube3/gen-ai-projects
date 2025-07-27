"""
Advanced ML-based Fraud Detection using XGBoost
Banking Fraud Detection MCP Server - Machine Learning Module
"""

import os
import pickle
import numpy as np
import pandas as pd
import duckdb
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
import warnings

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    from sklearn.ensemble import IsolationForest
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("ML libraries not available. Install with: uv add xgboost scikit-learn pandas numpy")

warnings.filterwarnings('ignore')

class MLFraudDetector:
    """Advanced ML-based fraud detection system using XGBoost and anomaly detection"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.model_dir = os.path.join(os.path.dirname(db_path), 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Model paths
        self.xgb_model_path = os.path.join(self.model_dir, 'xgb_fraud_model.json')
        self.scaler_path = os.path.join(self.model_dir, 'feature_scaler.joblib')
        self.isolation_model_path = os.path.join(self.model_dir, 'isolation_forest.joblib')
        self.label_encoders_path = os.path.join(self.model_dir, 'label_encoders.joblib')
        
        # Initialize models
        self.xgb_model = None
        self.scaler = None
        self.isolation_forest = None
        self.label_encoders = {}
        
        # Feature columns
        self.feature_columns = [
            'amount', 'hour', 'day_of_week', 'customer_age', 'customer_risk_score',
            'amount_zscore', 'freq_last_24h', 'avg_amount_last_7d', 'location_risk',
            'time_since_last_txn', 'amount_velocity', 'unusual_time', 'weekend_flag'
        ]
        
        self.categorical_features = ['location_encoded']
        
        if SKLEARN_AVAILABLE:
            self.load_or_train_models()
    
    def get_database_connection(self):
        """Get database connection"""
        return duckdb.connect(self.db_path)
    
    def extract_features(self, transaction_data: Dict) -> Dict[str, float]:
        """Extract comprehensive features for ML model"""
        if not SKLEARN_AVAILABLE:
            return self._simple_rule_based_features(transaction_data)
        
        conn = self.get_database_connection()
        
        try:
            # Basic transaction features
            amount = float(transaction_data.get('amount', 0))
            timestamp = pd.to_datetime(transaction_data.get('timestamp', datetime.now()))
            location = transaction_data.get('location', 'Unknown')
            customer_id = transaction_data.get('customer_id', '')
            
            # Time-based features
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            weekend_flag = 1 if day_of_week >= 5 else 0
            unusual_time = 1 if hour < 6 or hour > 22 else 0
            
            # Customer features
            customer_query = """
                SELECT age, risk_score 
                FROM customer_profiles 
                WHERE customer_id = ?
            """
            customer_data = conn.execute(customer_query, (customer_id,)).fetchone()
            customer_age = customer_data[0] if customer_data else 35
            customer_risk_score = customer_data[1] if customer_data else 0.5
            
            # Historical transaction features
            hist_query = """
                SELECT amount, timestamp, location
                FROM transactions 
                WHERE customer_id = ? AND timestamp < ?
                ORDER BY timestamp DESC
                LIMIT 100
            """
            # Convert timestamp to string for comparison (database stores as VARCHAR) 
            timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
            hist_txns = conn.execute(hist_query, (customer_id, timestamp_str)).fetchall()
            
            # Calculate historical statistics
            if hist_txns:
                hist_amounts = [float(txn[0]) for txn in hist_txns]
                hist_timestamps = [pd.to_datetime(txn[1]) for txn in hist_txns]
                
                # Amount statistics
                avg_amount_last_7d = np.mean([amt for amt, ts in zip(hist_amounts, hist_timestamps) 
                                            if (timestamp - ts).days <= 7]) if hist_amounts else amount
                amount_std = np.std(hist_amounts) if len(hist_amounts) > 1 else 1
                amount_zscore = (amount - np.mean(hist_amounts)) / max(amount_std, 1) if hist_amounts else 0
                
                # Frequency features
                recent_24h = [ts for ts in hist_timestamps if (timestamp - ts).total_seconds() <= 86400]
                freq_last_24h = len(recent_24h)
                
                # Time since last transaction
                time_since_last_txn = (timestamp - hist_timestamps[0]).total_seconds() / 3600 if hist_timestamps else 24
                
                # Amount velocity (recent spending rate)
                recent_amounts = [amt for amt, ts in zip(hist_amounts, hist_timestamps) 
                                if (timestamp - ts).total_seconds() <= 3600]
                amount_velocity = sum(recent_amounts) if recent_amounts else 0
                
            else:
                avg_amount_last_7d = amount
                amount_zscore = 0
                freq_last_24h = 0
                time_since_last_txn = 24
                amount_velocity = 0
            
            # Location risk scoring
            location_risk_query = """
                SELECT COUNT(*) as fraud_count, COUNT(*) as total_count
                FROM transactions t
                WHERE t.location = ?
            """
            location_stats = conn.execute(location_risk_query, (location,)).fetchone()
            location_risk = 0.5  # Default risk
            if location_stats and location_stats[1] > 0:
                # Simple location risk based on historical data
                location_risk = min(0.1 + (location_stats[0] / max(location_stats[1], 1)) * 0.8, 0.9)
            
            # Encode location
            if 'location' not in self.label_encoders:
                self.label_encoders['location'] = LabelEncoder()
                # Fit with common locations
                common_locations = ['HomeCity', 'WorkCity', 'ShoppingMall', 'Airport', 'Unknown']
                self.label_encoders['location'].fit(common_locations)
            
            try:
                location_encoded = self.label_encoders['location'].transform([location])[0]
            except ValueError:
                # Handle unseen locations
                location_encoded = self.label_encoders['location'].transform(['Unknown'])[0]
            
            features = {
                'amount': amount,
                'hour': hour,
                'day_of_week': day_of_week,
                'customer_age': customer_age,
                'customer_risk_score': customer_risk_score,
                'amount_zscore': amount_zscore,
                'freq_last_24h': freq_last_24h,
                'avg_amount_last_7d': avg_amount_last_7d,
                'location_risk': location_risk,
                'time_since_last_txn': time_since_last_txn,
                'amount_velocity': amount_velocity,
                'unusual_time': unusual_time,
                'weekend_flag': weekend_flag,
                'location_encoded': location_encoded
            }
            
            conn.close()
            return features
            
        except Exception as e:
            conn.close()
            logging.error(f"Feature extraction error: {e}")
            return self._simple_rule_based_features(transaction_data)
    
    def _simple_rule_based_features(self, transaction_data: Dict) -> Dict[str, float]:
        """Fallback rule-based features when ML libraries are not available"""
        amount = float(transaction_data.get('amount', 0))
        timestamp = pd.to_datetime(transaction_data.get('timestamp', datetime.now()))
        location = transaction_data.get('location', 'Unknown')
        
        return {
            'amount': amount,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'customer_age': 35,  # Default
            'customer_risk_score': 0.5,  # Default
            'amount_zscore': 1 if amount > 1000 else 0,
            'freq_last_24h': 1,
            'avg_amount_last_7d': amount,
            'location_risk': 0.8 if location != 'HomeCity' else 0.2,
            'time_since_last_txn': 6,
            'amount_velocity': amount,
            'unusual_time': 1 if timestamp.hour < 6 or timestamp.hour > 22 else 0,
            'weekend_flag': 1 if timestamp.weekday() >= 5 else 0,
            'location_encoded': 1 if location != 'HomeCity' else 0
        }
    
    def generate_synthetic_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data with fraud labels"""
        np.random.seed(42)
        n_samples = 5000
        
        # Generate diverse transaction patterns
        data = []
        
        for i in range(n_samples):
            # Normal transactions (80%)
            if i < n_samples * 0.8:
                is_fraud = 0
                amount = np.random.lognormal(5, 1)  # Normal amounts
                # Generate more realistic temporal patterns
                hour = np.random.choice(range(8, 20), p=[1/12]*12)  # Business hours
                location_risk = np.random.uniform(0.1, 0.4)
                freq_last_24h = np.random.poisson(2)
                customer_risk_score = np.random.uniform(0.1, 0.5)
            else:
                # Fraudulent transactions (20%)
                is_fraud = 1
                amount = np.random.lognormal(7, 1.5)  # Higher amounts
                hour = np.random.choice(range(24))  # Any time
                location_risk = np.random.uniform(0.6, 0.9)
                freq_last_24h = np.random.poisson(8)  # Higher frequency
                customer_risk_score = np.random.uniform(0.5, 0.9)
            
            # Generate other features
            day_of_week = np.random.randint(0, 7)
            customer_age = np.random.randint(18, 80)
            amount_zscore = np.random.normal(0 if not is_fraud else 2, 1)
            avg_amount_last_7d = amount * np.random.uniform(0.5, 2)
            time_since_last_txn = np.random.exponential(6)
            amount_velocity = amount * np.random.uniform(0, 3) if is_fraud else amount * np.random.uniform(0, 1)
            unusual_time = 1 if hour < 6 or hour > 22 else 0
            weekend_flag = 1 if day_of_week >= 5 else 0
            location_encoded = np.random.randint(0, 5)
            
            data.append({
                'amount': amount,
                'hour': hour,
                'day_of_week': day_of_week,
                'customer_age': customer_age,
                'customer_risk_score': customer_risk_score,
                'amount_zscore': amount_zscore,
                'freq_last_24h': freq_last_24h,
                'avg_amount_last_7d': avg_amount_last_7d,
                'location_risk': location_risk,
                'time_since_last_txn': time_since_last_txn,
                'amount_velocity': amount_velocity,
                'unusual_time': unusual_time,
                'weekend_flag': weekend_flag,
                'location_encoded': location_encoded,
                'is_fraud': is_fraud
            })
        
        return pd.DataFrame(data)
    
    def train_models(self):
        """Train XGBoost and Isolation Forest models"""
        if not SKLEARN_AVAILABLE:
            logging.warning("ML libraries not available. Skipping model training.")
            return
        
        logging.info("Training ML fraud detection models...")
        
        # Generate training data
        df = self.generate_synthetic_training_data()
        
        # Prepare features and target
        X = df[self.feature_columns + self.categorical_features]
        y = df['is_fraud']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.xgb_model.fit(X_train_scaled, y_train)
        
        # Train Isolation Forest for anomaly detection
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        # Train on normal transactions only
        normal_transactions = X_train_scaled[y_train == 0]
        self.isolation_forest.fit(normal_transactions)
        
        # Evaluate models
        y_pred_xgb = self.xgb_model.predict(X_test_scaled)
        y_pred_proba_xgb = self.xgb_model.predict_proba(X_test_scaled)[:, 1]
        
        y_pred_isolation = self.isolation_forest.predict(X_test_scaled)
        y_pred_isolation_binary = (y_pred_isolation == -1).astype(int)
        
        logging.info("XGBoost Model Performance:")
        logging.info(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba_xgb):.3f}")
        logging.info(f"Classification Report:\n{classification_report(y_test, y_pred_xgb)}")
        
        logging.info("Isolation Forest Performance:")
        logging.info(f"Classification Report:\n{classification_report(y_test, y_pred_isolation_binary)}")
        
        # Save models
        self.save_models()
        logging.info("Models trained and saved successfully!")
    
    def save_models(self):
        """Save trained models to disk"""
        if not SKLEARN_AVAILABLE:
            return
        
        if self.xgb_model:
            self.xgb_model.save_model(self.xgb_model_path)
        
        if self.scaler:
            joblib.dump(self.scaler, self.scaler_path)
        
        if self.isolation_forest:
            joblib.dump(self.isolation_forest, self.isolation_model_path)
        
        if self.label_encoders:
            joblib.dump(self.label_encoders, self.label_encoders_path)
    
    def load_models(self):
        """Load trained models from disk"""
        if not SKLEARN_AVAILABLE:
            return
        
        try:
            if os.path.exists(self.xgb_model_path):
                self.xgb_model = xgb.XGBClassifier()
                self.xgb_model.load_model(self.xgb_model_path)
            
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
            
            if os.path.exists(self.isolation_model_path):
                self.isolation_forest = joblib.load(self.isolation_model_path)
            
            if os.path.exists(self.label_encoders_path):
                self.label_encoders = joblib.load(self.label_encoders_path)
            
            logging.info("ML models loaded successfully!")
            
        except Exception as e:
            logging.error(f"Error loading models: {e}")
            self.train_models()  # Retrain if loading fails
    
    def load_or_train_models(self):
        """Load existing models or train new ones"""
        if (os.path.exists(self.xgb_model_path) and 
            os.path.exists(self.scaler_path) and 
            os.path.exists(self.isolation_model_path)):
            self.load_models()
        else:
            self.train_models()
    
    def predict_fraud_ml(self, transaction_data: Dict) -> Dict[str, Any]:
        """Predict fraud using ML models"""
        if not SKLEARN_AVAILABLE or not self.xgb_model or not self.scaler:
            return self._rule_based_prediction(transaction_data)
        
        try:
            # Extract features
            features = self.extract_features(transaction_data)
            
            # Prepare feature vector
            feature_vector = np.array([features[col] for col in self.feature_columns + self.categorical_features]).reshape(1, -1)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # XGBoost prediction
            xgb_fraud_prob = self.xgb_model.predict_proba(feature_vector_scaled)[0, 1]
            xgb_prediction = self.xgb_model.predict(feature_vector_scaled)[0]
            
            # Isolation Forest anomaly detection
            anomaly_score = self.isolation_forest.decision_function(feature_vector_scaled)[0]
            is_anomaly = self.isolation_forest.predict(feature_vector_scaled)[0] == -1
            
            # Combine predictions
            combined_score = (xgb_fraud_prob * 0.7) + (0.3 if is_anomaly else 0.0)
            combined_score = min(combined_score, 1.0)
            
            # Determine risk level
            if combined_score >= 0.8:
                risk_level = "CRITICAL"
            elif combined_score >= 0.6:
                risk_level = "HIGH"
            elif combined_score >= 0.4:
                risk_level = "MEDIUM"
            elif combined_score >= 0.2:
                risk_level = "LOW"
            else:
                risk_level = "MINIMAL"
            
            # Feature importance for explanation
            feature_importance = dict(zip(self.feature_columns + self.categorical_features, 
                                        self.xgb_model.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Generate explanation
            explanations = []
            for feature, importance in top_features:
                if feature in features:
                    explanations.append(f"{feature}: {features[feature]:.2f} (importance: {importance:.3f})")
            
            return {
                "ml_fraud_probability": round(xgb_fraud_prob, 4),
                "anomaly_score": round(anomaly_score, 4),
                "is_anomaly": bool(is_anomaly),
                "combined_fraud_score": round(combined_score, 4),
                "risk_level": risk_level,
                "model_prediction": "FRAUD" if combined_score >= 0.5 else "LEGITIMATE",
                "confidence": round(abs(combined_score - 0.5) * 2, 3),
                "key_features": explanations,
                "feature_values": features,
                "model_type": "XGBoost + Isolation Forest"
            }
            
        except Exception as e:
            logging.error(f"ML prediction error: {e}")
            return self._rule_based_prediction(transaction_data)
    
    def _rule_based_prediction(self, transaction_data: Dict) -> Dict[str, Any]:
        """Fallback rule-based prediction"""
        amount = float(transaction_data.get('amount', 0))
        location = transaction_data.get('location', 'Unknown')
        timestamp = pd.to_datetime(transaction_data.get('timestamp', datetime.now()))
        
        # Simple rules
        score = 0.0
        explanations = []
        
        if amount > 5000:
            score += 0.4
            explanations.append("High transaction amount")
        
        if location not in ['HomeCity', 'WorkCity']:
            score += 0.3
            explanations.append("Unfamiliar location")
        
        if timestamp.hour < 6 or timestamp.hour > 22:
            score += 0.2
            explanations.append("Unusual transaction time")
        
        if timestamp.weekday() >= 5:  # Weekend
            score += 0.1
            explanations.append("Weekend transaction")
        
        risk_level = "HIGH" if score >= 0.6 else "MEDIUM" if score >= 0.3 else "LOW"
        
        return {
            "ml_fraud_probability": round(score, 4),
            "anomaly_score": 0.0,
            "is_anomaly": False,
            "combined_fraud_score": round(score, 4),
            "risk_level": risk_level,
            "model_prediction": "FRAUD" if score >= 0.5 else "LEGITIMATE",
            "confidence": round(abs(score - 0.5) * 2, 3),
            "key_features": explanations,
            "feature_values": {},
            "model_type": "Rule-based (ML models not available)"
        }
    
    def batch_predict(self, transactions: List[Dict]) -> List[Dict]:
        """Batch prediction for multiple transactions"""
        results = []
        for txn in transactions:
            prediction = self.predict_fraud_ml(txn)
            prediction['txn_id'] = txn.get('txn_id', 'unknown')
            results.append(prediction)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "xgboost_available": self.xgb_model is not None,
            "isolation_forest_available": self.isolation_forest is not None,
            "scaler_available": self.scaler is not None,
            "ml_libraries_available": SKLEARN_AVAILABLE,
            "feature_count": len(self.feature_columns) + len(self.categorical_features),
            "model_files_exist": {
                "xgboost": os.path.exists(self.xgb_model_path),
                "scaler": os.path.exists(self.scaler_path),
                "isolation_forest": os.path.exists(self.isolation_model_path),
                "label_encoders": os.path.exists(self.label_encoders_path)
            }
        }


def get_database_path():
    """Get the database path"""
    db_path = os.getenv('DATABASE_PATH', 'data/bank.db')
    if not os.path.isabs(db_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, db_path)
    return db_path


# Global ML detector instance
ml_detector = None

def get_ml_detector():
    """Get or create ML detector instance"""
    global ml_detector
    if ml_detector is None:
        db_path = get_database_path()
        ml_detector = MLFraudDetector(db_path)
    return ml_detector


def check_transaction_ml(txn_id: str) -> Dict[str, Any]:
    """Enhanced transaction checking with ML"""
    db_path = get_database_path()
    conn = duckdb.connect(db_path)
    
    try:
        # Get transaction data
        txn = conn.execute("SELECT * FROM transactions WHERE txn_id = ?", (txn_id,)).fetchone()
        if not txn:
            return {"error": "Transaction not found"}
        
        transaction_data = {
            "txn_id": txn[0],
            "customer_id": txn[1],
            "amount": txn[2],
            "location": txn[3],
            "timestamp": txn[4],
        }
        
        # Get ML prediction
        detector = get_ml_detector()
        ml_result = detector.predict_fraud_ml(transaction_data)
        
        # Combine with traditional result
        result = {
            "txn_id": txn_id,
            "customer_id": transaction_data["customer_id"],
            "amount": transaction_data["amount"],
            "location": transaction_data["location"],
            "timestamp": str(transaction_data["timestamp"]),
            "ml_analysis": ml_result,
            "recommendation": "BLOCK" if ml_result["combined_fraud_score"] >= 0.7 else 
                           "REVIEW" if ml_result["combined_fraud_score"] >= 0.4 else "APPROVE"
        }
        
        conn.close()
        return result
        
    except Exception as e:
        conn.close()
        logging.error(f"Error in ML fraud check: {e}")
        return {"error": f"Analysis failed: {str(e)}"}


def analyze_transaction_patterns() -> Dict[str, Any]:
    """Analyze transaction patterns using ML"""
    try:
        detector = get_ml_detector()
        db_path = get_database_path()
        conn = duckdb.connect(db_path)
        
        # Get all transactions
        transactions = conn.execute("SELECT * FROM transactions").fetchall()
        conn.close()
        
        if not transactions:
            return {"error": "No transactions found"}
        
        # Convert to list of dicts
        txn_list = []
        for txn in transactions:
            txn_list.append({
                "txn_id": txn[0],
                "customer_id": txn[1],
                "amount": txn[2],
                "location": txn[3],
                "timestamp": txn[4]
            })
        
        # Batch prediction
        predictions = detector.batch_predict(txn_list)
        
        # Analyze results
        fraud_count = sum(1 for p in predictions if p["combined_fraud_score"] >= 0.5)
        high_risk_count = sum(1 for p in predictions if p["risk_level"] in ["HIGH", "CRITICAL"])
        avg_fraud_score = np.mean([p["combined_fraud_score"] for p in predictions])
        
        # Top risky transactions
        risky_txns = sorted(predictions, key=lambda x: x["combined_fraud_score"], reverse=True)[:5]
        
        return {
            "total_transactions": len(predictions),
            "suspected_fraud": fraud_count,
            "high_risk_transactions": high_risk_count,
            "average_fraud_score": round(avg_fraud_score, 4),
            "fraud_rate": round(fraud_count / len(predictions) * 100, 2),
            "top_risky_transactions": [
                {
                    "txn_id": txn["txn_id"],
                    "fraud_score": txn["combined_fraud_score"],
                    "risk_level": txn["risk_level"],
                    "prediction": txn["model_prediction"]
                }
                for txn in risky_txns
            ],
            "model_info": detector.get_model_info()
        }
        
    except Exception as e:
        logging.error(f"Error in pattern analysis: {e}")
        return {"error": f"Pattern analysis failed: {str(e)}"}
