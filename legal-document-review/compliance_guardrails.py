#!/usr/bin/env python3
"""
Legal Compliance Guardrails Module
Integrates Guardrails for AI safety and compliance in legal document processing.
"""

from typing import Dict, List, Any, Optional, Union
import logging
import re
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

try:
    import guardrails as gd
    from guardrails import Guard
    from guardrails.validators import (
        ValidChoices,
        ValidLength,
        TwoWords,
        RegexMatch,
        ReadingTime,
        ProfanityFree,
        ToxicLanguage,
        RestrictToTopic,
        SimilarToDocument,
        CompetitorCheck
    )
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    logging.warning("Guardrails not available. Falling back to basic validation.")

from pydantic import BaseModel, Field, field_validator
import validators

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    """Legal compliance levels."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    ENTERPRISE = "enterprise"

class LegalDomain(Enum):
    """Legal practice domains."""
    CIVIL_PROCEDURE = "civil_procedure"
    CONSTITUTIONAL_LAW = "constitutional_law"
    CONTRACT_LAW = "contract_law"
    EMPLOYMENT_LAW = "employment_law"
    HOUSING_LAW = "housing_law"
    TORT_LAW = "tort_law"
    CRIMINAL_LAW = "criminal_law"
    FAMILY_LAW = "family_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CORPORATE_LAW = "corporate_law"

@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""
    violation_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    field: Optional[str] = None
    suggested_fix: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ComplianceReport:
    """Comprehensive compliance report."""
    is_compliant: bool
    violations: List[ComplianceViolation]
    warnings: List[str]
    recommendations: List[str]
    compliance_score: float  # 0.0 to 1.0
    timestamp: datetime
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class LegalDocumentModel(BaseModel):
    """Pydantic model for legal document validation."""
    title: str = Field(..., min_length=5, max_length=200, description="Document title")
    content: str = Field(..., min_length=50, description="Document content")
    category: str = Field(..., description="Legal category")
    jurisdiction: str = Field(..., description="Legal jurisdiction")
    confidentiality_level: str = Field(default="public", description="Confidentiality classification")
    contains_pii: bool = Field(default=False, description="Contains personally identifiable information")
    contains_privileged: bool = Field(default=False, description="Contains attorney-client privileged information")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        # Check for potentially problematic content
        if any(word in v.lower() for word in ['confidential', 'attorney-client', 'privileged']):
            logging.warning(f"Title contains sensitive keywords: {v}")
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if len(v.strip()) < 50:
            raise ValueError("Content must be at least 50 characters")
        return v.strip()
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        valid_categories = [domain.value for domain in LegalDomain]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return v

class LegalQueryModel(BaseModel):
    """Pydantic model for legal query validation."""
    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    user_role: str = Field(default="client", description="User role (client, attorney, paralegal, admin)")
    access_level: str = Field(default="public", description="Access level required")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        # Basic content filtering
        prohibited_patterns = [
            r'\b(hack|crack|illegal|fraud)\b',
            r'\b(ssn|social\s+security)\b',
            r'\b(\d{3}-\d{2}-\d{4})\b',  # SSN pattern
        ]
        
        for pattern in prohibited_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Query contains prohibited content: {pattern}")
        
        return v.strip()

class LegalComplianceGuardrails:
    """Main compliance guardrails system for legal document processing."""
    
    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.STANDARD):
        self.compliance_level = compliance_level
        self.guards = {}
        self.violation_log = []
        
        if GUARDRAILS_AVAILABLE:
            self._initialize_guardrails()
        else:
            logger.warning("Guardrails not available. Using basic validation only.")
    
    def _initialize_guardrails(self):
        """Initialize Guardrails guards for different scenarios."""
        try:
            # Document content guard
            self.guards['document_content'] = Guard.from_pydantic(
                output_class=LegalDocumentModel,
                description="Validates legal document content for compliance and safety."
            )
            
            # Query validation guard
            self.guards['query_validation'] = Guard.from_pydantic(
                output_class=LegalQueryModel,
                description="Validates user queries for legal document search."
            )
            
            # Response quality guard
            if self.compliance_level in [ComplianceLevel.STRICT, ComplianceLevel.ENTERPRISE]:
                self.guards['response_quality'] = Guard()
                self.guards['response_quality'].use(
                    ValidLength(min=10, max=2000, on_fail="reask"),
                    ProfanityFree(on_fail="filter"),
                    ToxicLanguage(threshold=0.8, on_fail="reask")
                )
            
            logger.info(f"Guardrails initialized for compliance level: {self.compliance_level.value}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Guardrails: {str(e)}")
            GUARDRAILS_AVAILABLE = False
    
    def validate_document(self, document: Dict[str, Any]) -> ComplianceReport:
        """Validate a legal document for compliance."""
        violations = []
        warnings = []
        recommendations = []
        
        try:
            # Basic validation using Pydantic
            doc_model = LegalDocumentModel(**document)
            
            # Additional compliance checks
            violations.extend(self._check_pii_content(document))
            violations.extend(self._check_privileged_content(document))
            violations.extend(self._check_confidentiality(document))
            violations.extend(self._check_content_quality(document))
            
            # Guardrails validation if available
            if GUARDRAILS_AVAILABLE and 'document_content' in self.guards:
                try:
                    self.guards['document_content'].validate(document)
                except Exception as e:
                    violations.append(ComplianceViolation(
                        violation_type="GUARDRAILS_VALIDATION",
                        severity="MEDIUM",
                        message=f"Guardrails validation failed: {str(e)}"
                    ))
            
            # Generate recommendations
            recommendations.extend(self._generate_recommendations(document, violations))
            
        except Exception as e:
            violations.append(ComplianceViolation(
                violation_type="VALIDATION_ERROR",
                severity="HIGH",
                message=f"Document validation failed: {str(e)}"
            ))
        
        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(violations)
        is_compliant = compliance_score >= 0.8  # 80% threshold
        
        report = ComplianceReport(
            is_compliant=is_compliant,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            compliance_score=compliance_score,
            timestamp=datetime.now()
        )
        
        # Log the report
        self._log_compliance_report(report)
        
        return report
    
    def validate_query(self, query: str, user_context: Dict[str, Any] = None) -> ComplianceReport:
        """Validate a user query for compliance."""
        violations = []
        warnings = []
        recommendations = []
        
        try:
            # Basic validation
            query_data = {
                "query": query,
                "user_role": user_context.get("role", "client") if user_context else "client",
                "access_level": user_context.get("access_level", "public") if user_context else "public"
            }
            
            query_model = LegalQueryModel(**query_data)
            
            # Additional query-specific checks
            violations.extend(self._check_query_appropriateness(query))
            violations.extend(self._check_access_permissions(query, user_context))
            
            # Guardrails validation if available
            if GUARDRAILS_AVAILABLE and 'query_validation' in self.guards:
                try:
                    self.guards['query_validation'].validate(query_data)
                except Exception as e:
                    violations.append(ComplianceViolation(
                        violation_type="QUERY_GUARDRAILS",
                        severity="MEDIUM",
                        message=f"Query guardrails validation failed: {str(e)}"
                    ))
            
        except Exception as e:
            violations.append(ComplianceViolation(
                violation_type="QUERY_VALIDATION_ERROR",
                severity="HIGH",
                message=f"Query validation failed: {str(e)}"
            ))
        
        compliance_score = self._calculate_compliance_score(violations)
        is_compliant = compliance_score >= 0.9  # Higher threshold for queries
        
        return ComplianceReport(
            is_compliant=is_compliant,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            compliance_score=compliance_score,
            timestamp=datetime.now()
        )
    
    def validate_response(self, response: str, context: Dict[str, Any] = None) -> ComplianceReport:
        """Validate AI-generated responses for compliance."""
        violations = []
        warnings = []
        recommendations = []
        
        try:
            # Basic response validation
            if len(response.strip()) < 10:
                violations.append(ComplianceViolation(
                    violation_type="RESPONSE_TOO_SHORT",
                    severity="MEDIUM",
                    message="Response is too short to be helpful"
                ))
            
            # Check for disclaimer requirements
            if not self._has_legal_disclaimer(response):
                warnings.append("Response should include appropriate legal disclaimers")
                recommendations.append("Add legal disclaimer to response")
            
            # Content quality checks
            violations.extend(self._check_response_quality(response))
            
            # Guardrails validation if available
            if (GUARDRAILS_AVAILABLE and 'response_quality' in self.guards and 
                self.compliance_level in [ComplianceLevel.STRICT, ComplianceLevel.ENTERPRISE]):
                try:
                    self.guards['response_quality'].validate(response)
                except Exception as e:
                    violations.append(ComplianceViolation(
                        violation_type="RESPONSE_GUARDRAILS",
                        severity="MEDIUM",
                        message=f"Response guardrails validation failed: {str(e)}"
                    ))
            
        except Exception as e:
            violations.append(ComplianceViolation(
                violation_type="RESPONSE_VALIDATION_ERROR",
                severity="HIGH",
                message=f"Response validation failed: {str(e)}"
            ))
        
        compliance_score = self._calculate_compliance_score(violations)
        is_compliant = compliance_score >= 0.85
        
        return ComplianceReport(
            is_compliant=is_compliant,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            compliance_score=compliance_score,
            timestamp=datetime.now()
        )
    
    def _check_pii_content(self, document: Dict[str, Any]) -> List[ComplianceViolation]:
        """Check for personally identifiable information."""
        violations = []
        content = document.get('content', '') + ' ' + document.get('title', '')
        
        # PII patterns
        pii_patterns = {
            'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
            'Credit Card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'Phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'Email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        for pii_type, pattern in pii_patterns.items():
            if re.search(pattern, content):
                violations.append(ComplianceViolation(
                    violation_type="PII_DETECTED",
                    severity="HIGH",
                    message=f"Potential {pii_type} detected in document content",
                    suggested_fix=f"Redact or anonymize {pii_type} information"
                ))
        
        return violations
    
    def _check_privileged_content(self, document: Dict[str, Any]) -> List[ComplianceViolation]:
        """Check for attorney-client privileged content."""
        violations = []
        content = document.get('content', '').lower()
        
        privileged_indicators = [
            'attorney-client', 'privileged', 'confidential communication',
            'legal advice', 'work product', 'litigation strategy'
        ]
        
        for indicator in privileged_indicators:
            if indicator in content:
                violations.append(ComplianceViolation(
                    violation_type="PRIVILEGED_CONTENT",
                    severity="CRITICAL",
                    message=f"Potential privileged content detected: {indicator}",
                    suggested_fix="Review and redact privileged information"
                ))
        
        return violations
    
    def _check_confidentiality(self, document: Dict[str, Any]) -> List[ComplianceViolation]:
        """Check confidentiality classification."""
        violations = []
        
        confidentiality = document.get('confidentiality_level', 'public')
        if confidentiality not in ['public', 'internal', 'confidential', 'restricted']:
            violations.append(ComplianceViolation(
                violation_type="INVALID_CONFIDENTIALITY",
                severity="MEDIUM",
                message=f"Invalid confidentiality level: {confidentiality}"
            ))
        
        return violations
    
    def _check_content_quality(self, document: Dict[str, Any]) -> List[ComplianceViolation]:
        """Check content quality and appropriateness."""
        violations = []
        content = document.get('content', '')
        
        # Check for minimum content requirements
        if len(content.split()) < 20:
            violations.append(ComplianceViolation(
                violation_type="INSUFFICIENT_CONTENT",
                severity="MEDIUM",
                message="Document content appears to be too brief"
            ))
        
        # Check for proper legal citation format (basic)
        if 'v.' in content and not re.search(r'\d+\s+[A-Z][a-z.]+\s+\d+', content):
            violations.append(ComplianceViolation(
                violation_type="IMPROPER_CITATION",
                severity="LOW",
                message="Legal citations may not follow proper format"
            ))
        
        return violations
    
    def _check_query_appropriateness(self, query: str) -> List[ComplianceViolation]:
        """Check if query is appropriate for legal context."""
        violations = []
        
        # Check for potentially harmful queries
        harmful_patterns = [
            r'\b(how to break|illegal|fraud|scam)\b',
            r'\b(evade|avoid paying|cheat)\b'
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                violations.append(ComplianceViolation(
                    violation_type="INAPPROPRIATE_QUERY",
                    severity="HIGH",
                    message=f"Query contains potentially inappropriate content"
                ))
        
        return violations
    
    def _check_access_permissions(self, query: str, user_context: Dict[str, Any] = None) -> List[ComplianceViolation]:
        """Check if user has appropriate access permissions."""
        violations = []
        
        if not user_context:
            return violations
        
        user_role = user_context.get('role', 'client')
        
        # Check for privileged content queries
        if any(word in query.lower() for word in ['privileged', 'confidential', 'attorney work product']):
            if user_role not in ['attorney', 'paralegal', 'admin']:
                violations.append(ComplianceViolation(
                    violation_type="INSUFFICIENT_ACCESS",
                    severity="HIGH",
                    message="User role insufficient for privileged content access"
                ))
        
        return violations
    
    def _check_response_quality(self, response: str) -> List[ComplianceViolation]:
        """Check quality of AI-generated responses."""
        violations = []
        
        # Check for hallucination indicators
        if re.search(r'I am certain|definitely|100%|guaranteed', response, re.IGNORECASE):
            violations.append(ComplianceViolation(
                violation_type="OVERCONFIDENT_LANGUAGE",
                severity="MEDIUM",
                message="Response contains overconfident language",
                suggested_fix="Use more qualified language with appropriate disclaimers"
            ))
        
        return violations
    
    def _has_legal_disclaimer(self, response: str) -> bool:
        """Check if response has appropriate legal disclaimers."""
        disclaimer_indicators = [
            'not legal advice', 'consult an attorney', 'for informational purposes',
            'disclaimer', 'legal counsel'
        ]
        
        return any(indicator in response.lower() for indicator in disclaimer_indicators)
    
    def _generate_recommendations(self, document: Dict[str, Any], violations: List[ComplianceViolation]) -> List[str]:
        """Generate recommendations based on violations."""
        recommendations = []
        
        if any(v.violation_type == "PII_DETECTED" for v in violations):
            recommendations.append("Implement PII detection and redaction procedures")
        
        if any(v.violation_type == "PRIVILEGED_CONTENT" for v in violations):
            recommendations.append("Establish privilege review process before document storage")
        
        if any(v.severity == "CRITICAL" for v in violations):
            recommendations.append("Immediate review required before document publication")
        
        return recommendations
    
    def _calculate_compliance_score(self, violations: List[ComplianceViolation]) -> float:
        """Calculate compliance score based on violations."""
        if not violations:
            return 1.0
        
        # Weight violations by severity
        severity_weights = {
            'LOW': 0.1,
            'MEDIUM': 0.3,
            'HIGH': 0.6,
            'CRITICAL': 1.0
        }
        
        total_weight = sum(severity_weights.get(v.severity, 0.5) for v in violations)
        max_possible = len(violations)  # Assuming all could be CRITICAL
        
        score = max(0.0, 1.0 - (total_weight / max(max_possible, 1)))
        return round(score, 3)
    
    def _log_compliance_report(self, report: ComplianceReport):
        """Log compliance report for audit purposes."""
        try:
            log_entry = {
                'timestamp': report.timestamp.isoformat(),
                'is_compliant': report.is_compliant,
                'compliance_score': report.compliance_score,
                'violation_count': len(report.violations),
                'critical_violations': len([v for v in report.violations if v.severity == 'CRITICAL']),
                'high_violations': len([v for v in report.violations if v.severity == 'HIGH'])
            }
            
            # In production, this could write to a compliance audit log
            logger.info(f"Compliance Report: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Failed to log compliance report: {str(e)}")
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get summary of compliance checks performed."""
        return {
            'compliance_level': self.compliance_level.value,
            'guardrails_available': GUARDRAILS_AVAILABLE,
            'total_violations_logged': len(self.violation_log),
            'guards_initialized': list(self.guards.keys()),
            'last_check': datetime.now().isoformat()
        }

# Example usage and testing
def demo_compliance_guardrails():
    """Demonstrate compliance guardrails functionality."""
    print("🛡️  Legal Compliance Guardrails Demo")
    print("=" * 50)
    
    # Initialize compliance system
    compliance = LegalComplianceGuardrails(ComplianceLevel.STANDARD)
    
    # Test document validation
    test_document = {
        'title': 'Employment Contract - Confidential',
        'content': 'This employment agreement contains sensitive information including SSN 123-45-6789 and attorney-client privileged communications regarding litigation strategy.',
        'category': 'employment_law',
        'jurisdiction': 'state',
        'confidentiality_level': 'confidential',
        'contains_pii': True,
        'contains_privileged': True
    }
    
    print("\n📄 Testing Document Validation:")
    doc_report = compliance.validate_document(test_document)
    print(f"Compliant: {doc_report.is_compliant}")
    print(f"Score: {doc_report.compliance_score}")
    print(f"Violations: {len(doc_report.violations)}")
    for violation in doc_report.violations:
        print(f"  - {violation.severity}: {violation.message}")
    
    # Test query validation
    print("\n🔍 Testing Query Validation:")
    test_query = "How to evade paying taxes legally?"
    user_context = {'role': 'client', 'access_level': 'public'}
    query_report = compliance.validate_query(test_query, user_context)
    print(f"Query Compliant: {query_report.is_compliant}")
    print(f"Score: {query_report.compliance_score}")
    
    # Test response validation
    print("\n💬 Testing Response Validation:")
    test_response = "I am 100% certain that you can definitely avoid all legal consequences. This is guaranteed legal advice."
    response_report = compliance.validate_response(test_response)
    print(f"Response Compliant: {response_report.is_compliant}")
    print(f"Score: {response_report.compliance_score}")
    
    # Get compliance summary
    print("\n📊 Compliance Summary:")
    summary = compliance.get_compliance_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    demo_compliance_guardrails()
