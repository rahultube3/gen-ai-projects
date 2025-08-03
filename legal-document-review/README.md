# AI-powered Legal Document Search RAG System with Compliance Guardrails

🏛️ A comprehensive AI-powered legal document search and retrieval system with integrated compliance monitoring and safety guardrails.

## 🎯 Overview

This system provides semantic search capabilities over legal documents using SentenceTransformers, enhanced with comprehensive compliance guardrails to ensure safe and appropriate use in legal contexts.

## ✨ Key Features

### 🔍 Advanced Search Capabilities
- **Semantic Search**: SentenceTransformers-based vector similarity search
- **Fallback Text Search**: Simple keyword matching when vector search unavailable
- **Category-based Organization**: Documents organized by legal domain
- **Multi-jurisdiction Support**: Federal, state, and common law documents

### 🛡️ Compliance & Safety Guardrails
- **PII Detection**: Automatic detection of personally identifiable information
- **Privilege Protection**: Identification of attorney-client privileged content
- **Role-based Access Control**: Different access levels for different user roles
- **Query Validation**: Pre-search compliance checking of user queries
- **Response Validation**: Post-generation compliance checking of AI responses
- **Audit Logging**: Comprehensive logging for compliance monitoring

### 🔐 Security Features
- **Content Classification**: Automatic confidentiality level assignment
- **Access Permission Filtering**: Results filtered based on user permissions
- **Legal Disclaimers**: Automatic addition of appropriate legal disclaimers
- **Toxicity Detection**: Basic profanity and toxic language filtering

### 📊 Monitoring & Reporting
- **Compliance Scoring**: Numerical compliance scores for all operations
- **Violation Tracking**: Detailed tracking of compliance violations
- **Audit Trail**: Complete audit trail of all system interactions
- **Performance Metrics**: Search performance and system health monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.13.5+
- MongoDB Atlas account
- Required Python packages (automatically installed)

### Installation

1. **Clone and Navigate**
   ```bash
   cd legal-document-review
   ```

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB Atlas URI and other settings
   ```

5. **Initialize Database**
   ```bash
   python db_setup.py
   ```

6. **Test the System**
   ```bash
   python main.py
   ```

## 🏗️ Architecture

### Core Components

1. **LegalDocumentRAG** (`main.py`)
   - Main RAG system with compliance integration
   - Search functionality with access control
   - Document retrieval and filtering

2. **LegalComplianceGuardrails** (`compliance_guardrails.py`)
   - Comprehensive compliance validation
   - PII and privilege detection
   - Query and response validation
   - Audit logging and reporting

3. **Database Setup** (`db_setup.py`)
   - MongoDB database initialization
   - Document vectorization and storage
   - Index creation and optimization

4. **API Server** (`api_server.py`)
   - FastAPI-based REST API
   - Comprehensive endpoint coverage
   - Error handling and validation

### Compliance Levels

- **BASIC**: Essential compliance checks only
- **STANDARD**: Recommended for most use cases (default)
- **STRICT**: Enhanced validation for sensitive environments
- **ENTERPRISE**: Maximum compliance for enterprise deployments

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
MONGO_DB_URI=your_mongodb_atlas_connection_string

# Compliance
COMPLIANCE_LEVEL=standard  # basic|standard|strict|enterprise
ENABLE_AUDIT_LOGGING=true
ENABLE_PII_DETECTION=true
ENABLE_PRIVILEGE_CHECK=true

# Security
ENABLE_ACCESS_CONTROL=true
SESSION_TIMEOUT_MINUTES=30

# Content Filtering
ENABLE_PROFANITY_FILTER=true
TOXICITY_THRESHOLD=0.8

# Legal Disclaimers
ENABLE_AUTO_DISCLAIMERS=true
```

### User Roles & Permissions

| Role | Access Levels | Capabilities |
|------|---------------|-------------|
| **Client** | Public | Basic document search |
| **Paralegal** | Public, Internal | Enhanced search access |
| **Attorney** | Public, Internal, Confidential | Privileged content access |
| **Admin** | All levels | Full system access |

## 📖 Usage Examples

### Basic Search
```python
from main import LegalDocumentRAG
from compliance_guardrails import ComplianceLevel

# Initialize with compliance
rag = LegalDocumentRAG(ComplianceLevel.STANDARD)

# Search with user context
user_context = {'role': 'attorney', 'access_level': 'confidential'}
result = rag.search_documents(
    "contract formation requirements", 
    top_k=5, 
    user_context=user_context
)

print(f"Compliant: {result['search_allowed']}")
print(f"Results: {len(result['results'])}")
```

### Document Validation
```python
from compliance_guardrails import LegalComplianceGuardrails

compliance = LegalComplianceGuardrails()

document = {
    'title': 'Employment Agreement',
    'content': 'Standard employment terms...',
    'category': 'employment_law',
    'jurisdiction': 'state'
}

report = compliance.validate_document(document)
print(f"Compliance Score: {report.compliance_score}")
print(f"Violations: {len(report.violations)}")
```

### API Usage
```bash
# Health check
curl http://localhost:8000/health

# Search documents
curl -X POST http://localhost:8000/search 
  -H "Content-Type: application/json" 
  -d '{
    "query": "eviction notice requirements",
    "max_results": 3,
    "user_role": "attorney",
    "access_level": "confidential"
  }'

# Validate document
curl -X POST http://localhost:8000/validate-document 
  -H "Content-Type: application/json" 
  -d '{
    "title": "Contract Sample",
    "content": "This is a sample contract...",
    "category": "contract_law",
    "jurisdiction": "state"
  }'
```

## 🚀 API Server

Start the FastAPI server:

```bash
python api_server.py
```

Access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

- `GET /health` - System health and compliance status
- `POST /search` - Search documents with compliance validation
- `POST /validate-document` - Validate document compliance
- `GET /categories` - List available document categories
- `GET /compliance/summary` - Compliance monitoring summary
- `GET /compliance/audit-log` - Audit trail access

## 🛡️ Compliance Features

### PII Detection
Automatically detects and flags:
- Social Security Numbers
- Credit Card Numbers
- Phone Numbers
- Email Addresses

### Privilege Protection
Identifies potentially privileged content:
- Attorney-client communications
- Work product materials
- Litigation strategy discussions
- Confidential legal advice

### Query Validation
Pre-search validation includes:
- Content appropriateness checking
- Access permission verification
- Prohibited pattern detection
- Role-based filtering

### Response Validation
Post-generation validation includes:
- Content quality assessment
- Legal disclaimer requirements
- Overconfident language detection
- Compliance scoring

## 📊 Monitoring & Auditing

### Compliance Metrics
- Overall compliance score
- Violation counts by severity
- Access pattern analysis
- Query success rates

### Audit Logging
- All search queries logged
- User access patterns tracked
- Compliance violations recorded
- Performance metrics captured

### Reporting
- Real-time compliance dashboards
- Periodic compliance reports
- Violation trend analysis
- User access summaries

## 🔧 Technical Details

### Vector Store
- **Technology**: SentenceTransformers with scikit-learn
- **Dimensions**: 384 features (configurable)
- **Similarity**: Cosine similarity
- **Fallback**: Keyword-based text search

### Database
- **Technology**: MongoDB Atlas
- **Security**: SSL/TLS encryption
- **Indexing**: Text and vector indexes
- **Backup**: Automated backups

### Performance
- **Search Speed**: Sub-second response times
- **Concurrency**: Multi-user support
- **Caching**: Configurable result caching
- **Scaling**: Horizontal scaling support

## 🔒 Security Considerations

### Data Protection
- All connections encrypted (SSL/TLS)
- PII detection and redaction
- Privilege protection mechanisms
- Access control enforcement

### Authentication & Authorization
- Role-based access control (RBAC)
- Session management
- API key authentication (configurable)
- Audit trail for all access

### Compliance Standards
- Legal industry best practices
- Data privacy regulations (GDPR, CCPA)
- Attorney-client privilege protection
- Professional responsibility compliance

## 🚀 Deployment

### Development
```bash
python main.py              # Local testing
python api_server.py         # API server
```

### Production
- Use production-grade WSGI server (e.g., Gunicorn)
- Configure proper SSL certificates
- Set up monitoring and alerting
- Enable comprehensive audit logging
- Implement backup strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure compliance checks pass
6. Submit a pull request

## ⚖️ Legal Notice

This system is designed to assist with legal document research and analysis. It does not provide legal advice and should not be used as a substitute for consultation with qualified legal professionals. Users are responsible for ensuring compliance with applicable laws and regulations in their jurisdiction.

## 🆘 Support

For technical support, compliance questions, or feature requests:

- Create an issue on GitHub
- Review the documentation
- Check the compliance guidelines
- Consult the API documentation

---

🏛️ **Built for Legal Professionals, Secured by Design, Compliant by Default**