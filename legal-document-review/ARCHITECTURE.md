# Legal Document Review System - Technical Architecture

## 🏗️ **System Architecture Overview**

The Legal Document Review System follows a modern, layered architecture pattern with clear separation of concerns, ensuring maintainability, scalability, and security. The system is designed around the principles of Domain-Driven Design (DDD) and Clean Architecture.

## 📐 **Architectural Patterns**

### **1. Layered Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Angular UI    │    │     FastAPI REST API           │ │
│  │   (Frontend)    │    │   (API Gateway & Controllers)  │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   RAG Engine    │    │   Compliance Guardrails        │ │
│  │   (Core Logic)  │    │   (Business Rules & Policies)  │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     Data Access Layer                       │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   MongoDB       │    │    Vector Storage              │ │
│  │   (Documents)   │    │    (TF-IDF Models)             │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### **2. Domain Model**
```
┌─────────────────────────────────────────────────────────────┐
│                      Domain Entities                        │
├─────────────────────────────────────────────────────────────┤
│  LegalDocument    │  SearchQuery      │  ComplianceReport   │
│  ├─ id            │  ├─ query         │  ├─ timestamp       │
│  ├─ title         │  ├─ max_results   │  ├─ violations      │
│  ├─ text          │  ├─ user_role     │  ├─ compliance_level│
│  ├─ category      │  ├─ access_level  │  ├─ search_allowed  │
│  ├─ jurisdiction  │  └─ filters       │  └─ recommendations │
│  ├─ metadata      │                   │                     │
│  └─ vectors       │  SearchResult     │  AuditLog           │
│                   │  ├─ documents     │  ├─ user_id         │
│  User             │  ├─ total_found   │  ├─ action          │
│  ├─ user_id       │  ├─ search_time   │  ├─ timestamp       │
│  ├─ role          │  ├─ compliance    │  ├─ details         │
│  ├─ access_level  │  └─ recommendations│  └─ metadata       │
│  └─ permissions   │                   │                     │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **Component Architecture**

### **1. Frontend Architecture (Angular)**

#### **Component Hierarchy**
```
AppComponent (Root)
├── ChatComponent (Main Interface)
│   ├── MessageListComponent
│   ├── MessageInputComponent
│   └── SettingsPanelComponent
├── HeaderComponent
└── FooterComponent
```

#### **Service Layer**
```
├── LegalRagService (Core API Communication)
│   ├── searchDocuments()
│   ├── getCategories()
│   ├── getHealthStatus()
│   └── sendMessage()
├── AuthService (Authentication)
├── ConfigService (Configuration)
└── ErrorHandlingService (Global Error Management)
```

#### **State Management**
```
Application State
├── User State
│   ├── authentication status
│   ├── user role and permissions
│   └── session information
├── UI State
│   ├── loading states
│   ├── error messages
│   └── notification queue
└── Data State
    ├── chat messages
    ├── search results
    └── available categories
```

### **2. Backend Architecture (FastAPI)**

#### **API Layer Structure**
```
FastAPI Application
├── Routers
│   ├── /api/v1/search       (Document search endpoints)
│   ├── /api/v1/documents    (Document management)
│   ├── /api/v1/categories   (Category management)
│   ├── /api/v1/compliance   (Compliance reporting)
│   └── /api/v1/health       (System health monitoring)
├── Middleware
│   ├── CORS Middleware      (Cross-origin requests)
│   ├── Authentication       (Bearer token validation)
│   ├── Request Logging      (Audit trail)
│   └── Error Handling       (Global exception management)
└── Dependencies
    ├── Database Connection  (MongoDB client)
    ├── RAG System Instance  (Singleton pattern)
    └── Security Dependencies (Token validation)
```

#### **Core Services**
```
Business Services
├── DocumentService
│   ├── search_documents()
│   ├── get_document_by_id()
│   ├── validate_document()
│   └── index_document()
├── ComplianceService
│   ├── check_compliance()
│   ├── generate_report()
│   ├── log_activity()
│   └── validate_access()
├── UserService
│   ├── authenticate_user()
│   ├── check_permissions()
│   └── log_user_activity()
└── SearchService
    ├── execute_search()
    ├── rank_results()
    ├── apply_filters()
    └── generate_suggestions()
```

### **3. RAG Engine Architecture**

#### **Core Components**
```
LegalDocumentRAG
├── Initialization
│   ├── MongoDB connection setup
│   ├── TF-IDF vectorizer loading
│   ├── Compliance system initialization
│   └── Index validation
├── Search Pipeline
│   ├── Query preprocessing
│   ├── Vector similarity calculation
│   ├── Result ranking and scoring
│   ├── Compliance filtering
│   └── Response formatting
├── Indexing Pipeline
│   ├── Document preprocessing
│   ├── Text extraction and cleaning
│   ├── Vector generation
│   ├── Metadata extraction
│   └── Database storage
└── Maintenance
    ├── Index optimization
    ├── Performance monitoring
    ├── Error recovery
    └── Backup and restore
```

#### **Search Algorithm Flow**
```
Search Request
    ↓
Query Validation & Preprocessing
    ↓
User Permission Check
    ↓
TF-IDF Vector Generation
    ↓
Similarity Score Calculation
    ↓
Initial Result Ranking
    ↓
Compliance Filtering
    ↓
Final Result Ranking
    ↓
Response Formatting
    ↓
Audit Logging
    ↓
Return Results
```

### **4. Compliance System Architecture**

#### **Guardrails Framework**
```
LegalComplianceGuardrails
├── Compliance Levels
│   ├── BASIC      (Essential protections)
│   ├── STANDARD   (Professional requirements)
│   ├── STRICT     (Enhanced security)
│   └── ENTERPRISE (Maximum protection)
├── Validation Modules
│   ├── ContentValidator      (Content appropriateness)
│   ├── PIIDetector          (Personal information)
│   ├── PrivilegeChecker     (Attorney-client privilege)
│   ├── ConfidentialityGuard (Sensitive information)
│   └── EthicsValidator      (Professional ethics)
├── Risk Assessment
│   ├── ViolationDetector    (Policy violations)
│   ├── RiskScorer           (Risk level calculation)
│   ├── RecommendationEngine (Mitigation suggestions)
│   └── AlertSystem          (Real-time notifications)
└── Audit System
    ├── ActivityLogger       (User actions)
    ├── ComplianceReporter   (Violation reports)
    ├── MetricsCollector     (System metrics)
    └── ExportService        (Audit exports)
```

## 🗄️ **Database Architecture**

### **MongoDB Schema Design**

#### **Collections Structure**
```
legal_documents_db
├── legal_documents
│   ├── _id (ObjectId)
│   ├── title (String, indexed)
│   ├── text (String, full-text indexed)
│   ├── category (String, indexed)
│   ├── jurisdiction (String, indexed)
│   ├── confidentiality_level (String)
│   ├── contains_pii (Boolean)
│   ├── contains_privileged (Boolean)
│   ├── metadata (Object)
│   ├── created_at (DateTime)
│   └── updated_at (DateTime)
├── vectorizer_data
│   ├── _id (ObjectId)
│   ├── model_type (String)
│   ├── vocabulary (Array)
│   ├── idf_values (Array)
│   ├── feature_names (Array)
│   ├── created_at (DateTime)
│   └── version (String)
├── audit_logs
│   ├── _id (ObjectId)
│   ├── user_id (String, indexed)
│   ├── action (String, indexed)
│   ├── resource (String)
│   ├── timestamp (DateTime, indexed)
│   ├── ip_address (String)
│   ├── user_agent (String)
│   ├── request_data (Object)
│   ├── response_status (Number)
│   └── compliance_check (Object)
└── user_sessions
    ├── _id (ObjectId)
    ├── user_id (String, indexed)
    ├── session_token (String, hashed)
    ├── created_at (DateTime)
    ├── expires_at (DateTime)
    ├── last_activity (DateTime)
    └── metadata (Object)
```

#### **Indexing Strategy**
```
Performance Indexes
├── legal_documents
│   ├── text_index: { title: "text", text: "text" }
│   ├── category_index: { category: 1 }
│   ├── jurisdiction_index: { jurisdiction: 1 }
│   ├── compound_index: { category: 1, jurisdiction: 1 }
│   └── timestamp_index: { created_at: -1 }
├── audit_logs
│   ├── user_timestamp: { user_id: 1, timestamp: -1 }
│   ├── action_index: { action: 1 }
│   └── timestamp_index: { timestamp: -1 }
└── user_sessions
    ├── user_id_index: { user_id: 1 }
    ├── token_index: { session_token: 1 }
    └── expiry_index: { expires_at: 1 }
```

## 🔐 **Security Architecture**

### **Authentication & Authorization**
```
Security Layer
├── Authentication
│   ├── Bearer Token Validation
│   ├── Session Management
│   ├── Token Expiration Handling
│   └── Secure Token Storage
├── Authorization
│   ├── Role-Based Access Control (RBAC)
│   │   ├── Client Role      (Basic search access)
│   │   ├── Paralegal Role   (Enhanced search + documents)
│   │   ├── Attorney Role    (Full access + privileged docs)
│   │   └── Admin Role       (System management)
│   ├── Permission Matrix
│   │   ├── Document Access Levels
│   │   ├── Search Scope Permissions
│   │   ├── Export Permissions
│   │   └── Administrative Permissions
│   └── Resource-Level Security
│       ├── Document-Level Permissions
│       ├── Category-Based Access
│       └── Jurisdiction-Based Filtering
└── Data Protection
    ├── Input Validation & Sanitization
    ├── SQL/NoSQL Injection Prevention
    ├── XSS Protection
    ├── CSRF Protection
    └── Rate Limiting
```

### **Compliance Security Model**
```
Compliance Framework
├── Data Classification
│   ├── Public Documents
│   ├── Internal Documents
│   ├── Confidential Documents
│   ├── Privileged Documents
│   └── PII-Containing Documents
├── Access Controls
│   ├── Need-to-Know Basis
│   ├── Least Privilege Principle
│   ├── Separation of Duties
│   └── Regular Access Review
├── Audit & Monitoring
│   ├── Real-Time Activity Monitoring
│   ├── Compliance Violation Detection
│   ├── Automated Alert System
│   └── Comprehensive Audit Trails
└── Data Handling
    ├── Encryption at Rest
    ├── Encryption in Transit
    ├── Secure Data Processing
    └── Data Retention Policies
```

## 🚀 **Deployment Architecture**

### **Development Environment**
```
Development Stack
├── Local Development
│   ├── Python 3.8+ Virtual Environment
│   ├── MongoDB Local Instance
│   ├── FastAPI Development Server
│   └── Angular Development Server
├── Testing Environment
│   ├── pytest Test Suite
│   ├── Test Database
│   ├── Mock External Services
│   └── Compliance Test Cases
└── Development Tools
    ├── VS Code / PyCharm
    ├── MongoDB Compass
    ├── Postman/Insomnia
    └── Git Version Control
```

### **Production Environment**
```
Production Infrastructure
├── Application Tier
│   ├── Docker Containers
│   │   ├── FastAPI Application
│   │   ├── Background Workers
│   │   └── Health Monitoring
│   ├── Load Balancer (Nginx/ALB)
│   ├── Auto-scaling Groups
│   └── Container Orchestration (Docker Swarm/K8s)
├── Database Tier
│   ├── MongoDB Atlas Cluster
│   │   ├── Primary Replica Set
│   │   ├── Secondary Replicas
│   │   └── Backup Strategy
│   ├── Connection Pooling
│   └── Database Monitoring
├── Frontend Tier
│   ├── Static File Hosting (CDN)
│   ├── Angular Production Build
│   ├── HTTPS Termination
│   └── Cache Management
└── Monitoring & Logging
    ├── Application Performance Monitoring
    ├── Error Tracking & Alerting
    ├── Log Aggregation
    └── Security Monitoring
```

## 📊 **Data Flow Architecture**

### **Search Request Flow**
```
User Search Request
    ↓
[Angular Frontend]
    ↓ HTTP Request
[FastAPI Router] → [Authentication Middleware]
    ↓                    ↓
[Request Validation] → [Authorization Check]
    ↓                    ↓
[RAG Service] → [Compliance Validation]
    ↓                    ↓
[MongoDB Query] → [Vector Similarity]
    ↓                    ↓
[Result Ranking] → [Compliance Filtering]
    ↓                    ↓
[Response Format] → [Audit Logging]
    ↓                    ↓
[HTTP Response] ← [Activity Log]
    ↓
[Angular Display]
```

### **Document Indexing Flow**
```
Document Upload
    ↓
[Document Validation]
    ↓
[Text Extraction & Cleaning]
    ↓
[Metadata Extraction]
    ↓
[Compliance Classification]
    ↓
[TF-IDF Vector Generation]
    ↓
[MongoDB Storage]
    ↓
[Search Index Update]
    ↓
[Completion Notification]
```

## 🔄 **Integration Architecture**

### **External Integrations**
```
External Systems
├── Authentication Providers
│   ├── OAuth 2.0 / OpenID Connect
│   ├── LDAP/Active Directory
│   ├── SAML SSO
│   └── Multi-Factor Authentication
├── Document Sources
│   ├── Legal Database APIs
│   ├── File System Integrations
│   ├── Cloud Storage (S3, Azure)
│   └── Document Management Systems
├── Compliance Systems
│   ├── Legal Ethics Databases
│   ├── Regulatory Compliance APIs
│   ├── Audit Systems
│   └── Risk Management Platforms
└── Monitoring & Analytics
    ├── Application Performance Monitoring
    ├── Business Intelligence Tools
    ├── Log Management Systems
    └── Security Information & Event Management
```

### **API Integration Patterns**
```
Integration Patterns
├── RESTful APIs
│   ├── Standard HTTP Methods
│   ├── JSON Request/Response
│   ├── Stateless Communication
│   └── Resource-Based URLs
├── Event-Driven Architecture
│   ├── Document Processing Events
│   ├── Compliance Alert Events
│   ├── User Activity Events
│   └── System Health Events
├── Batch Processing
│   ├── Bulk Document Import
│   ├── Periodic Index Updates
│   ├── Compliance Report Generation
│   └── Data Cleanup Tasks
└── Real-Time Communication
    ├── WebSocket Connections
    ├── Real-Time Search Updates
    ├── Live Compliance Monitoring
    └── Instant Notifications
```

## 📈 **Performance Architecture**

### **Scalability Strategy**
```
Scalability Approach
├── Horizontal Scaling
│   ├── Stateless Application Design
│   ├── Load Balancer Distribution
│   ├── Database Read Replicas
│   └── Microservice Decomposition
├── Vertical Scaling
│   ├── Resource Optimization
│   ├── Memory Management
│   ├── CPU Utilization
│   └── Storage Performance
├── Caching Strategy
│   ├── Application-Level Caching
│   ├── Database Query Caching
│   ├── Static Content CDN
│   └── Session Storage Optimization
└── Performance Monitoring
    ├── Response Time Tracking
    ├── Throughput Measurement
    ├── Resource Utilization
    └── Bottleneck Identification
```

### **Optimization Techniques**
```
Performance Optimizations
├── Database Optimizations
│   ├── Strategic Indexing
│   ├── Query Optimization
│   ├── Connection Pooling
│   └── Aggregation Pipeline Tuning
├── Application Optimizations
│   ├── Asynchronous Processing
│   ├── Memory Efficient Algorithms
│   ├── Lazy Loading Strategies
│   └── Background Task Processing
├── Frontend Optimizations
│   ├── Code Splitting
│   ├── Lazy Module Loading
│   ├── Asset Optimization
│   └── Progressive Web App Features
└── Network Optimizations
    ├── Compression (Gzip/Brotli)
    ├── Content Delivery Network
    ├── HTTP/2 Support
    └── Request/Response Optimization
```

---

**Document Version**: 1.0  
**Last Updated**: July 31, 2025  
**Architecture Status**: Production Ready  
**Review Cycle**: Quarterly
