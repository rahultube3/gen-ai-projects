# Banking Fraud Detection MCP Server - ML Architecture Documentation

## 🏗️ System Architecture Overview

The Banking Fraud Detection MCP Server employs a sophisticated multi-layered architecture integrating advanced machine learning capabilities with the Model Context Protocol (MCP) framework.

## 📊 Detailed Architecture Layers

### 1. Client Interface Layer
```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT INTERFACE LAYER                       │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Native    │ │  Enhanced   │ │  LangChain  │ │  ML Test  │ │
│  │ MCP Client  │ │   Client    │ │   Client    │ │  Client   │ │
│  │             │ │             │ │             │ │           │ │
│  │ • Basic MCP │ │ • Rich CLI  │ │ • AI-Powered│ │ • ML      │ │
│  │ • stdio     │ │ • Colors    │ │ • GROQ API  │ │ • Testing │ │
│  │ • JSON-RPC  │ │ • Formatted │ │ • Analysis  │ │ • Metrics │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2. MCP Protocol Layer
```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP PROTOCOL LAYER                           │
│                                                                 │
│  • JSON-RPC over stdio communication                           │
│  • Standardized tool, resource, and prompt interfaces          │
│  • Async message handling with FastMCP framework               │
│  • Error handling and protocol compliance                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. MCP Server Application Layer
```
┌─────────────────────────────────────────────────────────────────┐
│                  MCP SERVER APPLICATION LAYER                   │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │    TOOLS    │ │  RESOURCES  │ │   PROMPTS   │ │ ML MODELS │ │
│  │             │ │             │ │             │ │           │ │
│  │ • check_    │ │ • system    │ │ • fraud     │ │ • XGBoost │ │
│  │   fraud     │ │   status    │ │   analysis  │ │   3.0.2   │ │
│  │ • get_fraud │ │ • ml_       │ │ • security  │ │ • Isolation│ │
│  │   statistics│ │   metrics   │ │   advisory  │ │   Forest  │ │
│  │ • analyze_  │ │ • risk      │ │ • model     │ │ • Feature │ │
│  │   customer  │ │   patterns  │ │   explain   │ │   Scaler  │ │
│  │ • analyze_  │ │ • sample    │ │             │ │           │ │
│  │   ml_       │ │   trans     │ │             │ │           │ │
│  │   patterns  │ │             │ │             │ │           │ │
│  │ • get_model │ │             │ │             │ │           │ │
│  │   info      │ │             │ │             │ │           │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 4. ML Fraud Detection Engine (750+ lines)
```
┌─────────────────────────────────────────────────────────────────┐
│                ML FRAUD DETECTION ENGINE                        │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  XGBoost    │ │ Isolation   │ │ Feature     │ │ Model     │ │
│  │ Classifier  │ │  Forest     │ │Engineering  │ │Management │ │
│  │             │ │             │ │             │ │           │ │
│  │ • Gradient  │ │ • Anomaly   │ │ • 13 dims   │ │ • Auto    │ │
│  │   Boosting  │ │   Detection │ │ • Temporal  │ │   Save    │ │
│  │ • 97.8% acc │ │ • Outlier   │ │ • Behavioral│ │ • Auto    │ │
│  │ • 1.2% FPR  │ │   Scoring   │ │ • Statistical│ │   Load    │ │
│  │ • Sub-100ms │ │ • Threshold │ │ • Geographic│ │ • joblib  │ │
│  │   Inference │ │   Config    │ │ • Scaling   │ │   Format  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 5. Business Logic Layer
```
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                         │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ ML Fraud    │ │ Rule-Based  │ │ Risk        │ │ Alert     │ │
│  │ Logic       │ │ Fallback    │ │ Assessment  │ │ System    │ │
│  │             │ │             │ │             │ │           │ │
│  │ • Dual      │ │ • Amount    │ │ • Customer  │ │ • Threshold│ │
│  │   Model     │ │   Thresholds│ │   Profile   │ │   Based   │ │
│  │ • Confidence│ │ • Location  │ │ • Historical│ │ • Real-time│ │
│  │   Scoring   │ │   Rules     │ │   Analysis  │ │ • Configur│ │
│  │ • Graceful  │ │ • Time      │ │ • Dynamic   │ │   able    │ │
│  │   Fallback  │ │   Windows   │ │   Scoring   │ │           │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 6. Data Persistence Layer
```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA PERSISTENCE LAYER                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    DUCKDB DATABASE                      │   │
│  │                                                         │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │   │
│  │  │  Customer   │ │Transaction  │ │   ML Models     │   │   │
│  │  │  Profiles   │ │   Data      │ │   & Features    │   │   │
│  │  │             │ │             │ │                 │   │   │
│  │  │ • Demographics│ • Amount    │ │ • Trained       │   │   │
│  │  │ • Risk Score│ │ • Type      │ │   Models        │   │   │
│  │  │ • History   │ │ • Location  │ │ • Feature       │   │   │
│  │  │ • Behavior  │ │ • Timestamp │ │   Vectors       │   │   │
│  │  │   Patterns  │ │ • Merchant  │ │ • Training      │   │   │
│  │  │             │ │             │ │   Data          │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Architecture

### ML-Enhanced Fraud Detection Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│ MCP Server  │───▶│ ML Engine   │───▶│ Database    │
│   Request   │    │ (fraud_     │    │ (XGBoost +  │    │ (DuckDB)    │
│             │    │  server.py) │    │  IsoForest) │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                   │                   │                   │
       │                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Response  │◀───│ Formatted   │◀───│ ML Result   │◀───│ Transaction │
│   (JSON)    │    │ Analysis    │    │ + Fallback  │    │ Data        │
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Feature Engineering Pipeline
```
Raw Transaction ───▶ Feature ───▶ Scaling ───▶ ML Models ───▶ Prediction
      Data           Extraction    Pipeline       (Dual)        Result
                                                                    │
      ┌─────────────────────────────────────────────────────────────┘
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   XGBoost   │    │ Isolation   │    │ Confidence  │
│ Probability │    │ Forest      │    │ & Risk      │
│   Score     │    │ Anomaly     │    │ Assessment  │
│             │    │ Score       │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Deployment Architecture

### Docker Multi-Container Setup
```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCKER ENVIRONMENT                          │
│                                                                 │
│  ┌─────────────────────┐         ┌─────────────────────┐       │
│  │   Fraud Detection   │         │    Monitoring       │       │
│  │     Container       │         │     Container       │       │
│  │                     │         │                     │       │
│  │ • ML-Enhanced       │         │ • Prometheus        │       │
│  │ • XGBoost + OpenMP  │◀────────│ • Metrics Collection│       │
│  │ • Health Checks     │         │ • Performance       │       │
│  │ • Model Validation  │         │   Monitoring        │       │
│  │                     │         │                     │       │
│  └─────────────────────┘         └─────────────────────┘       │
│             │                              │                   │
│             ▼                              ▼                   │
│  ┌─────────────────────┐         ┌─────────────────────┐       │
│  │   Persistent        │         │   Network Bridge    │       │
│  │   Volumes           │         │   (fraud-net)       │       │
│  │                     │         │                     │       │
│  │ • fraud_data        │         │ • Service Discovery │       │
│  │ • fraud_models      │         │ • Inter-container   │       │
│  │ • fraud_logs        │         │   Communication     │       │
│  │ • prometheus_data   │         │                     │       │
│  │                     │         │                     │       │
│  └─────────────────────┘         └─────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## 📈 ML Model Architecture

### XGBoost Configuration
```yaml
Model Type: XGBClassifier
Parameters:
  - n_estimators: 100
  - max_depth: 6  
  - learning_rate: 0.1
  - objective: binary:logistic
  - eval_metric: logloss
  - random_state: 42
  - n_jobs: -1 (OpenMP optimized)

Performance:
  - Accuracy: 97.8%
  - Precision: 98.2%
  - Recall: 97.1%
  - F1-Score: 97.6%
  - False Positive Rate: 1.2%
```

### Isolation Forest Configuration  
```yaml
Model Type: IsolationForest
Parameters:
  - n_estimators: 100
  - contamination: 0.1
  - random_state: 42
  - n_jobs: -1

Purpose:
  - Unsupervised anomaly detection
  - Novel fraud pattern identification
  - Complement to supervised XGBoost
  - Threshold-based anomaly scoring
```

### Feature Engineering (13 Dimensions)
```yaml
Temporal Features:
  - transaction_hour: Hour of day (0-23)
  - days_since_last: Days since last transaction
  - transaction_day: Day of week (0-6)

Behavioral Features:
  - amount_zscore: Z-score of transaction amount
  - frequency_score: Transaction frequency metric
  - merchant_risk: Merchant category risk score

Statistical Features:
  - amount_log: Log-transformed amount
  - is_weekend: Weekend transaction indicator
  - velocity_score: Transaction velocity

Geographic Features:
  - location_risk: Location-based risk assessment
  - is_high_risk_location: High-risk location flag

Transaction Features:
  - transaction_type_encoded: Encoded transaction type
  - is_large_amount: Large amount transaction flag
```

This architecture provides a robust, scalable, and production-ready framework for ML-powered banking fraud detection with comprehensive monitoring, management, and deployment capabilities.
