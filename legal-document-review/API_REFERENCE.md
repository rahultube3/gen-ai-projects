# AI-powered Legal Document Search API - Reference Documentation

## 📚 **API Overview**

The AI-powered Legal Document Search API is a RESTful web service that provides secure, compliant access to legal document search and retrieval functionality. Built with FastAPI, it offers high-performance document search with integrated compliance guardrails.

## 🌐 **Base Information**

| Attribute | Value |
|-----------|-------|
| **Base URL** | `http://localhost:8000` (Development) |
| **API Version** | `v1` |
| **Content Type** | `application/json` |
| **Authentication** | Bearer Token |
| **Documentation** | `/docs` (Swagger UI) |
| **OpenAPI Spec** | `/openapi.json` |

## 🔐 **Authentication**

All API endpoints (except health check) require authentication using Bearer tokens.

### **Authorization Header**
```http
Authorization: Bearer <your_token_here>
```

### **User Roles**
- `client` - Basic search access
- `paralegal` - Enhanced search capabilities
- `attorney` - Full access including privileged documents
- `admin` - System administration access

## 📋 **API Endpoints**

### **1. Health & Status**

#### **GET /health**
Returns the current health status of the API and its dependencies.

**Request:**
```http
GET /health
Content-Type: application/json
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-31T00:49:00.442585",
  "compliance_level": "standard",
  "guardrails_available": true,
  "database_connected": true,
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is unhealthy

---

### **2. Document Categories**

#### **GET /categories**
Retrieves all available legal document categories.

**Request:**
```http
GET /categories
Authorization: Bearer <token>
Content-Type: application/json
```

**Response:**
```json
{
  "categories": [
    "administrative_law",
    "banking_law",
    "civil_procedure",
    "constitutional_law",
    "contract_law",
    "corporate_law",
    "criminal_law",
    "employment_law",
    "environmental_law",
    "family_law",
    "healthcare_law",
    "housing_law",
    "immigration_law",
    "insurance_law",
    "intellectual_property",
    "tax_law",
    "tort_law"
  ],
  "total": 17
}
```

**Status Codes:**
- `200 OK` - Categories retrieved successfully
- `401 Unauthorized` - Invalid or missing token
- `500 Internal Server Error` - Server error

---

### **3. Document Search**

#### **POST /search**
Performs semantic search across legal documents with compliance filtering.

**Request:**
```http
POST /search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "contract breach remedies",
  "max_results": 10,
  "user_role": "attorney",
  "access_level": "confidential",
  "category_filter": "contract_law",
  "jurisdiction_filter": "federal"
}
```

**Request Body Schema:**
```json
{
  "query": "string (required, 3-500 characters)",
  "max_results": "integer (optional, 1-20, default: 5)",
  "user_role": "string (optional, default: 'client')",
  "access_level": "string (optional, default: 'public')",
  "category_filter": "string (optional)",
  "jurisdiction_filter": "string (optional)",
  "min_similarity": "float (optional, 0.0-1.0, default: 0.1)"
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": "doc_12345",
      "title": "Contract Remedies and Breach of Contract",
      "text": "When a party breaches a contract, several remedies are available...",
      "category": "contract_law",
      "jurisdiction": "federal",
      "similarity": 0.85,
      "confidentiality_level": "public",
      "contains_pii": false,
      "contains_privileged": false,
      "compliance_checked": true,
      "disclaimer_added": true,
      "access_timestamp": "2025-07-31T00:49:00.442585"
    }
  ],
  "compliance_report": {
    "compliance_level": "standard",
    "violations_found": 0,
    "warnings": [],
    "recommendations": [],
    "search_allowed": true,
    "filtered_count": 0,
    "total_violations": 0
  },
  "search_allowed": true,
  "total_results": 1,
  "search_duration_seconds": 0.234,
  "message": "Search completed successfully"
}
```

**Status Codes:**
- `200 OK` - Search completed successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

### **4. Document Validation**

#### **POST /validate-document**
Validates document content against compliance policies.

**Request:**
```http
POST /validate-document
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Employment Contract Template",
  "text": "This employment agreement is between...",
  "category": "employment_law",
  "jurisdiction": "state",
  "user_role": "attorney",
  "compliance_level": "strict"
}
```

**Request Body Schema:**
```json
{
  "title": "string (required)",
  "text": "string (required)",
  "category": "string (optional)",
  "jurisdiction": "string (optional)",
  "user_role": "string (optional, default: 'client')",
  "compliance_level": "string (optional, default: 'standard')"
}
```

**Response:**
```json
{
  "is_valid": true,
  "compliance_report": {
    "compliance_level": "strict",
    "violations_found": 0,
    "warnings": [
      {
        "type": "missing_clause",
        "message": "Consider adding a confidentiality clause",
        "severity": "low",
        "recommendation": "Add standard confidentiality language"
      }
    ],
    "recommendations": [
      "Review termination clause language",
      "Ensure compliance with local employment laws"
    ],
    "search_allowed": true,
    "filtered_count": 0,
    "total_violations": 0
  },
  "contains_pii": false,
  "contains_privileged": true,
  "suggested_category": "employment_law",
  "confidence_score": 0.92
}
```

**Status Codes:**
- `200 OK` - Validation completed
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Invalid or missing token
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

### **5. Compliance Reporting**

#### **GET /compliance/report**
Generates a comprehensive compliance report for audit purposes.

**Request:**
```http
GET /compliance/report?start_date=2025-07-01&end_date=2025-07-31&user_id=user123
Authorization: Bearer <token>
Content-Type: application/json
```

**Query Parameters:**
- `start_date` (optional): Start date for report (YYYY-MM-DD)
- `end_date` (optional): End date for report (YYYY-MM-DD)
- `user_id` (optional): Specific user ID to include
- `compliance_level` (optional): Filter by compliance level
- `include_violations` (optional): Include violation details (default: true)

**Response:**
```json
{
  "report_id": "report_789",
  "generated_at": "2025-07-31T00:49:00.442585",
  "period": {
    "start_date": "2025-07-01T00:00:00",
    "end_date": "2025-07-31T23:59:59"
  },
  "summary": {
    "total_searches": 1250,
    "total_violations": 15,
    "violation_rate": 0.012,
    "compliance_rate": 0.988,
    "users_affected": 3
  },
  "violations": [
    {
      "id": "violation_001",
      "timestamp": "2025-07-15T14:30:00",
      "user_id": "user123",
      "violation_type": "unauthorized_access",
      "severity": "medium",
      "description": "Attempted access to privileged document without authorization",
      "action_taken": "Access denied, user notified",
      "resolved": true
    }
  ],
  "recommendations": [
    "Review user permissions for elevated access",
    "Implement additional training for document classification",
    "Consider stricter compliance level for sensitive documents"
  ],
  "compliance_metrics": {
    "documents_scanned": 50000,
    "pii_detections": 125,
    "privilege_protections": 89,
    "content_filters_applied": 234
  }
}
```

**Status Codes:**
- `200 OK` - Report generated successfully
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions for compliance reports
- `400 Bad Request` - Invalid date parameters
- `500 Internal Server Error` - Server error

---

### **6. User Activity Logs**

#### **GET /logs/activity**
Retrieves user activity logs for audit and monitoring purposes.

**Request:**
```http
GET /logs/activity?limit=50&offset=0&user_id=user123&action=search
Authorization: Bearer <token>
Content-Type: application/json
```

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 50, max: 1000)
- `offset` (optional): Number of records to skip (default: 0)
- `user_id` (optional): Filter by specific user
- `action` (optional): Filter by action type (search, access, validate, etc.)
- `start_date` (optional): Start date filter (YYYY-MM-DD)
- `end_date` (optional): End date filter (YYYY-MM-DD)

**Response:**
```json
{
  "logs": [
    {
      "id": "log_456",
      "user_id": "user123",
      "action": "search",
      "timestamp": "2025-07-31T00:49:00.442585",
      "resource": "/search",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "request_data": {
        "query": "contract breach",
        "category": "contract_law"
      },
      "response_status": 200,
      "compliance_check": {
        "passed": true,
        "violations": 0
      },
      "duration_ms": 234
    }
  ],
  "total_count": 1250,
  "page_info": {
    "limit": 50,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  }
}
```

**Status Codes:**
- `200 OK` - Logs retrieved successfully
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions for activity logs
- `400 Bad Request` - Invalid query parameters
- `500 Internal Server Error` - Server error

---

## 📊 **Error Handling**

### **Standard Error Response**
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-07-31T00:49:00.442585",
  "request_id": "req_12345",
  "suggestions": [
    "Check your authentication token",
    "Verify request parameters"
  ]
}
```

### **Common Error Codes**

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Request parameters are invalid |
| 401 | `UNAUTHORIZED` | Authentication required or failed |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### **Validation Error Response**
```json
{
  "detail": [
    {
      "loc": ["query"],
      "msg": "String too short",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 3}
    }
  ],
  "error_code": "VALIDATION_ERROR"
}
```

## 🔄 **Rate Limiting**

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1627776000
X-RateLimit-Window: 3600
```

### **Rate Limits by Role**

| Role | Requests/Hour | Search/Hour | Burst Limit |
|------|---------------|-------------|-------------|
| client | 100 | 50 | 10/minute |
| paralegal | 500 | 200 | 25/minute |
| attorney | 1000 | 500 | 50/minute |
| admin | 2000 | 1000 | 100/minute |

## 📝 **Request/Response Examples**

### **Example 1: Basic Document Search**

**Request:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "intellectual property licensing",
    "max_results": 5,
    "user_role": "attorney"
  }'
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": "ip_license_001",
      "title": "Software Licensing Agreement Template",
      "text": "This software licensing agreement governs...",
      "category": "intellectual_property",
      "jurisdiction": "federal",
      "similarity": 0.91,
      "confidentiality_level": "public",
      "contains_pii": false,
      "contains_privileged": false
    }
  ],
  "total_results": 1,
  "search_duration_seconds": 0.156
}
```

### **Example 2: Category-Filtered Search**

**Request:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "employment termination procedures",
    "max_results": 10,
    "category_filter": "employment_law",
    "user_role": "paralegal",
    "min_similarity": 0.3
  }'
```

### **Example 3: Document Validation**

**Request:**
```bash
curl -X POST "http://localhost:8000/validate-document" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Non-Disclosure Agreement",
    "text": "This NDA is between Company A and Company B...",
    "category": "contract_law",
    "compliance_level": "strict"
  }'
```

## 🛡️ **Security Considerations**

### **Best Practices**
1. **Always use HTTPS** in production environments
2. **Validate and sanitize** all input data
3. **Implement proper authentication** for all requests
4. **Use appropriate user roles** for access control
5. **Monitor rate limits** to prevent abuse
6. **Log all activities** for audit trails
7. **Regularly rotate** authentication tokens

### **Data Privacy**
- All requests are logged for compliance purposes
- Personal information is automatically detected and protected
- Privileged attorney-client communications are safeguarded
- Search results are filtered based on user permissions

### **Compliance Requirements**
- All API usage must comply with legal ethics rules
- Document access is restricted based on confidentiality levels
- Audit trails are maintained for all user activities
- Compliance reports are available for regulatory review

---

**API Version**: 1.0.0  
**Last Updated**: July 31, 2025  
**Documentation Status**: Complete  
**Contact**: Legal Tech Team
