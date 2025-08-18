#!/usr/bin/env python3
"""
Comprehensive Guardrails System for HR Assistant
Implements security, privacy, content filtering, and compliance controls
"""

import re
import logging
import hashlib
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk assessment levels for queries and responses"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ViolationType(Enum):
    """Types of policy violations"""
    PII_EXPOSURE = "pii_exposure"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    CONFIDENTIAL_INFO = "confidential_info"
    SECURITY_RISK = "security_risk"
    RATE_LIMIT = "rate_limit"
    COMPLIANCE_VIOLATION = "compliance_violation"

@dataclass
class GuardrailViolation:
    """Represents a guardrail violation"""
    violation_type: ViolationType
    risk_level: RiskLevel
    message: str
    details: str
    timestamp: datetime
    user_id: Optional[str] = None
    query: Optional[str] = None

class HRGuardrails:
    """
    Comprehensive guardrails system for HR Assistant
    Implements security, privacy, and compliance controls
    """
    
    def __init__(self):
        self.violations_log = []
        self.rate_limit_cache = {}
        self.blocked_patterns = self._load_blocked_patterns()
        self.pii_patterns = self._load_pii_patterns()
        self.confidential_keywords = self._load_confidential_keywords()
        
    def _load_blocked_patterns(self) -> List[re.Pattern]:
        """Load patterns for inappropriate content detection"""
        patterns = [
            # Profanity and inappropriate language
            r'\b(damn|hell|crap|stupid|idiot)\b',
            # Harassment keywords
            r'\b(harass|discriminat|bully|threaten)\b',
            # Personal attacks
            r'\b(you\s+(are|suck|fail)|hate\s+you)\b',
            # Inappropriate personal questions
            r'\b(personal\s+life|dating|relationship|sexual)\b',
            # System manipulation attempts
            r'\b(ignore\s+instructions|forget\s+previous|system\s+prompt)\b',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _load_pii_patterns(self) -> List[re.Pattern]:
        """Load patterns for PII detection"""
        patterns = [
            # Social Security Numbers
            r'\b\d{3}-\d{2}-\d{4}\b',
            r'\b\d{9}\b',
            # Phone numbers
            r'\b\d{3}-\d{3}-\d{4}\b',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            # Email addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Credit card numbers (basic pattern)
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            # Driver's license patterns (varies by state)
            r'\b[A-Z]\d{7,14}\b',
            # Bank account numbers
            r'\b\d{8,17}\b',
            # Address patterns
            r'\b\d+\s+[A-Za-z\s]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln)\b',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _load_confidential_keywords(self) -> List[str]:
        """Load keywords that indicate confidential information"""
        return [
            'salary', 'wage', 'compensation', 'bonus', 'raise', 'promotion',
            'termination', 'firing', 'layoff', 'disciplinary', 'investigation',
            'lawsuit', 'legal action', 'settlement', 'complaint',
            'confidential', 'proprietary', 'trade secret', 'internal only',
            'executive', 'board', 'merger', 'acquisition',
            'performance review', 'rating', 'evaluation score',
            'medical', 'disability', 'accommodation', 'leave of absence',
            'discrimination', 'harassment', 'complaint', 'grievance'
        ]
    
    def validate_query(self, query: str, user_id: Optional[str] = None) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Validate a user query against all guardrails
        Returns (is_allowed, violations)
        """
        violations = []
        
        # Rate limiting check
        if not self._check_rate_limit(user_id):
            violations.append(GuardrailViolation(
                violation_type=ViolationType.RATE_LIMIT,
                risk_level=RiskLevel.MEDIUM,
                message="Rate limit exceeded",
                details="Too many requests in short time period",
                timestamp=datetime.now(),
                user_id=user_id,
                query=query[:100] + "..." if len(query) > 100 else query
            ))
        
        # Content filtering
        content_violations = self._check_content_filter(query)
        violations.extend(content_violations)
        
        # PII detection
        pii_violations = self._check_pii_exposure(query)
        violations.extend(pii_violations)
        
        # Security checks
        security_violations = self._check_security_risks(query)
        violations.extend(security_violations)
        
        # Log violations
        for violation in violations:
            self.violations_log.append(violation)
            logger.warning(f"Guardrail violation: {violation.violation_type.value} - {violation.message}")
        
        # Determine if query is allowed
        critical_violations = [v for v in violations if v.risk_level == RiskLevel.CRITICAL]
        is_allowed = len(critical_violations) == 0
        
        return is_allowed, violations
    
    def validate_response(self, response: str, query: str, user_id: Optional[str] = None) -> Tuple[str, List[GuardrailViolation]]:
        """
        Validate and potentially modify a response before sending to user
        Returns (filtered_response, violations)
        """
        violations = []
        filtered_response = response
        
        # PII sanitization
        filtered_response, pii_violations = self._sanitize_pii_in_response(filtered_response)
        violations.extend(pii_violations)
        
        # Confidential information check
        conf_violations = self._check_confidential_info(filtered_response)
        violations.extend(conf_violations)
        
        # Content appropriateness
        content_violations = self._check_response_content(filtered_response)
        violations.extend(content_violations)
        
        # Add disclaimer for sensitive topics
        if self._contains_sensitive_topic(filtered_response):
            filtered_response = self._add_hr_disclaimer(filtered_response)
        
        # Log violations
        for violation in violations:
            self.violations_log.append(violation)
            logger.warning(f"Response violation: {violation.violation_type.value} - {violation.message}")
        
        return filtered_response, violations
    
    def _check_rate_limit(self, user_id: Optional[str], max_requests: int = 20, window_minutes: int = 5) -> bool:
        """Check if user has exceeded rate limits"""
        if not user_id:
            user_id = "anonymous"
        
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=window_minutes)
        
        # Clean old entries
        if user_id in self.rate_limit_cache:
            self.rate_limit_cache[user_id] = [
                timestamp for timestamp in self.rate_limit_cache[user_id]
                if timestamp > window_start
            ]
        else:
            self.rate_limit_cache[user_id] = []
        
        # Check if limit exceeded
        if len(self.rate_limit_cache[user_id]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limit_cache[user_id].append(current_time)
        return True
    
    def _check_content_filter(self, text: str) -> List[GuardrailViolation]:
        """Check for inappropriate content"""
        violations = []
        
        for pattern in self.blocked_patterns:
            if pattern.search(text):
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.INAPPROPRIATE_CONTENT,
                    risk_level=RiskLevel.HIGH,
                    message="Inappropriate content detected",
                    details=f"Content contains blocked pattern: {pattern.pattern}",
                    timestamp=datetime.now(),
                    query=text[:100] + "..." if len(text) > 100 else text
                ))
        
        return violations
    
    def _check_pii_exposure(self, text: str) -> List[GuardrailViolation]:
        """Check for PII in user input"""
        violations = []
        
        for pattern in self.pii_patterns:
            matches = pattern.findall(text)
            if matches:
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.PII_EXPOSURE,
                    risk_level=RiskLevel.CRITICAL,
                    message="PII detected in input",
                    details=f"Found {len(matches)} potential PII matches",
                    timestamp=datetime.now(),
                    query="[REDACTED - PII DETECTED]"
                ))
        
        return violations
    
    def _check_security_risks(self, text: str) -> List[GuardrailViolation]:
        """Check for security-related risks"""
        violations = []
        
        # SQL injection patterns
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC)\b)',
            r'(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)',
            r'(\'|\";|--|\#)'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.SECURITY_RISK,
                    risk_level=RiskLevel.CRITICAL,
                    message="Potential SQL injection detected",
                    details=f"Security pattern matched: {pattern}",
                    timestamp=datetime.now(),
                    query=text[:100] + "..." if len(text) > 100 else text
                ))
        
        # Script injection patterns
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'onload\s*=',
            r'eval\s*\(',
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.SECURITY_RISK,
                    risk_level=RiskLevel.HIGH,
                    message="Potential script injection detected",
                    details=f"Script pattern matched: {pattern}",
                    timestamp=datetime.now(),
                    query=text[:100] + "..." if len(text) > 100 else text
                ))
        
        return violations
    
    def _sanitize_pii_in_response(self, response: str) -> Tuple[str, List[GuardrailViolation]]:
        """Remove or mask PII from responses"""
        violations = []
        sanitized_response = response
        
        for pattern in self.pii_patterns:
            matches = pattern.findall(sanitized_response)
            if matches:
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.PII_EXPOSURE,
                    risk_level=RiskLevel.HIGH,
                    message="PII removed from response",
                    details=f"Sanitized {len(matches)} PII instances",
                    timestamp=datetime.now()
                ))
                # Replace with placeholder
                sanitized_response = pattern.sub("[REDACTED]", sanitized_response)
        
        return sanitized_response, violations
    
    def _check_confidential_info(self, response: str) -> List[GuardrailViolation]:
        """Check for confidential information in responses"""
        violations = []
        
        for keyword in self.confidential_keywords:
            if keyword.lower() in response.lower():
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.CONFIDENTIAL_INFO,
                    risk_level=RiskLevel.MEDIUM,
                    message="Potentially confidential information detected",
                    details=f"Response contains sensitive keyword: {keyword}",
                    timestamp=datetime.now()
                ))
        
        return violations
    
    def _check_response_content(self, response: str) -> List[GuardrailViolation]:
        """Check response content for appropriateness"""
        violations = []
        
        # Check for blocked patterns in response
        for pattern in self.blocked_patterns:
            if pattern.search(response):
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.INAPPROPRIATE_CONTENT,
                    risk_level=RiskLevel.HIGH,
                    message="Inappropriate content in response",
                    details=f"Response contains blocked pattern: {pattern.pattern}",
                    timestamp=datetime.now()
                ))
        
        return violations
    
    def _contains_sensitive_topic(self, response: str) -> bool:
        """Check if response contains sensitive HR topics"""
        sensitive_topics = [
            'salary', 'compensation', 'disciplinary', 'termination',
            'legal', 'lawsuit', 'discrimination', 'harassment',
            'medical', 'disability', 'mental health'
        ]
        
        return any(topic.lower() in response.lower() for topic in sensitive_topics)
    
    def _add_hr_disclaimer(self, response: str) -> str:
        """Add appropriate disclaimer for sensitive HR topics"""
        disclaimer = ("\n\n⚠️ **Disclaimer**: This information is for general guidance only. "
                     "For specific situations involving compensation, disciplinary actions, "
                     "legal matters, or personal circumstances, please consult with HR directly "
                     "or seek appropriate professional advice.")
        
        return response + disclaimer
    
    def get_violations_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of violations in the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_violations = [v for v in self.violations_log if v.timestamp > cutoff_time]
        
        summary = {
            'total_violations': len(recent_violations),
            'by_type': {},
            'by_risk_level': {},
            'unique_users': set(),
            'time_period_hours': hours
        }
        
        for violation in recent_violations:
            # Count by type
            vtype = violation.violation_type.value
            summary['by_type'][vtype] = summary['by_type'].get(vtype, 0) + 1
            
            # Count by risk level
            risk = violation.risk_level.value
            summary['by_risk_level'][risk] = summary['by_risk_level'].get(risk, 0) + 1
            
            # Track unique users
            if violation.user_id:
                summary['unique_users'].add(violation.user_id)
        
        summary['unique_users'] = len(summary['unique_users'])
        return summary
    
    def clear_old_logs(self, days: int = 30):
        """Clear violation logs older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.violations_log = [v for v in self.violations_log if v.timestamp > cutoff_time]
        logger.info(f"Cleared violation logs older than {days} days")

# Global guardrails instance
hr_guardrails = HRGuardrails()

def validate_query(query: str, user_id: Optional[str] = None) -> Tuple[bool, List[GuardrailViolation]]:
    """Convenience function for query validation"""
    return hr_guardrails.validate_query(query, user_id)

def validate_response(response: str, query: str, user_id: Optional[str] = None) -> Tuple[str, List[GuardrailViolation]]:
    """Convenience function for response validation"""
    return hr_guardrails.validate_response(response, query, user_id)

def get_violations_summary(hours: int = 24) -> Dict[str, Any]:
    """Convenience function for violations summary"""
    return hr_guardrails.get_violations_summary(hours)

if __name__ == "__main__":
    # Test the guardrails system
    test_queries = [
        "What are the health insurance benefits?",
        "My SSN is 123-45-6789, can you help me?",
        "You are stupid and I hate this system",
        "SELECT * FROM users WHERE password = 'admin'",
        "What's the CEO's salary?",
    ]
    
    print("🛡️ Testing HR Guardrails System")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        is_allowed, violations = validate_query(query, "test_user")
        print(f"Allowed: {is_allowed}")
        for violation in violations:
            print(f"  - {violation.violation_type.value}: {violation.message}")
    
    print(f"\n📊 Violations Summary:")
    summary = get_violations_summary()
    print(f"Total violations: {summary['total_violations']}")
    print(f"By type: {summary['by_type']}")
    print(f"By risk level: {summary['by_risk_level']}")
