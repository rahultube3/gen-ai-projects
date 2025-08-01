"""
Advanced Privacy Redaction System
Features: Configurable Rules, Compliance Standards, Performance Optimization, Context-Aware Redaction
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import json
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class RedactionLevel(Enum):
    """Redaction security levels"""
    LOW = "low"           # Basic redaction
    MEDIUM = "medium"     # Standard compliance
    HIGH = "high"         # Maximum privacy
    CUSTOM = "custom"     # User-defined rules

class ComplianceStandard(Enum):
    """Compliance standards for redaction"""
    PCI_DSS = "pci_dss"   # Payment Card Industry
    GDPR = "gdpr"         # General Data Protection Regulation
    HIPAA = "hipaa"       # Health Insurance Portability
    SOX = "sox"           # Sarbanes-Oxley Act
    CCPA = "ccpa"         # California Consumer Privacy Act

@dataclass
class RedactionRule:
    """Individual redaction rule configuration"""
    name: str
    pattern: str
    replacement: str
    enabled: bool = True
    compliance_standards: List[ComplianceStandard] = field(default_factory=list)
    priority: int = 0  # Higher priority rules execute first
    context_aware: bool = False
    preserve_format: bool = False

@dataclass
class RedactionResult:
    """Result of redaction operation"""
    original_text: str
    redacted_text: str
    redactions_made: Dict[str, int]
    risk_score: float
    compliance_violations: List[str]
    processing_time_ms: float

class AdvancedRedactionEngine:
    """Advanced redaction engine with configurable rules and compliance features"""
    
    def __init__(self, level: RedactionLevel = RedactionLevel.MEDIUM):
        self.level = level
        self.rules: List[RedactionRule] = []
        self.custom_rules: List[RedactionRule] = []
        self.performance_stats = {
            "total_redactions": 0,
            "total_processing_time": 0.0,
            "rules_applied": {}
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
        # Compile patterns for performance
        self._compiled_patterns = {}
        self._compile_patterns()
    
    def _initialize_default_rules(self):
        """Initialize comprehensive default redaction rules"""
        
        # Financial Information Rules
        financial_rules = [
            RedactionRule(
                name="credit_card_full",
                pattern=r'\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                replacement="[REDACTED_CARD]",
                compliance_standards=[ComplianceStandard.PCI_DSS],
                priority=10
            ),
            RedactionRule(
                name="credit_card_masked",
                pattern=r'\b\d{4}[-\s*x]{1,3}\d{4}[-\s*x]{1,3}\d{4}[-\s*x]{1,3}\d{4}\b',
                replacement="[REDACTED_CARD]",
                compliance_standards=[ComplianceStandard.PCI_DSS],
                priority=9
            ),
            RedactionRule(
                name="bank_account",
                pattern=r'\b\d{8,17}\b',
                replacement="[REDACTED_ACCOUNT]",
                compliance_standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.SOX],
                priority=8
            ),
            RedactionRule(
                name="routing_number",
                pattern=r'\b[0-9]{9}\b',
                replacement="[REDACTED_ROUTING]",
                compliance_standards=[ComplianceStandard.PCI_DSS],
                priority=7
            ),
            RedactionRule(
                name="large_amounts",
                pattern=r'\$([1-9]\d{3,}(?:\.\d{2})?)',
                replacement="$[REDACTED_AMOUNT]",
                compliance_standards=[ComplianceStandard.SOX],
                priority=3
            )
        ]
        
        # Personal Information Rules
        personal_rules = [
            RedactionRule(
                name="ssn_full",
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                replacement="[REDACTED_SSN]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.HIPAA],
                priority=10
            ),
            RedactionRule(
                name="ssn_no_dash",
                pattern=r'\b\d{9}\b',
                replacement="[REDACTED_SSN]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.HIPAA],
                priority=9
            ),
            RedactionRule(
                name="phone_parentheses",
                pattern=r'\(\d{3}\)\s?\d{3}-\d{4}',
                replacement="[REDACTED_PHONE]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.CCPA],
                priority=6
            ),
            RedactionRule(
                name="phone_dashes",
                pattern=r'\b\d{3}-\d{3}-\d{4}\b',
                replacement="[REDACTED_PHONE]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.CCPA],
                priority=6
            ),
            RedactionRule(
                name="phone_dots",
                pattern=r'\b\d{3}\.\d{3}\.\d{4}\b',
                replacement="[REDACTED_PHONE]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.CCPA],
                priority=6
            ),
            RedactionRule(
                name="email_address",
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                replacement="[REDACTED_EMAIL]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.CCPA],
                priority=5
            )
        ]
        
        # Address and Location Rules
        location_rules = [
            RedactionRule(
                name="zip_code",
                pattern=r'\b\d{5}(?:-\d{4})?\b',
                replacement="[REDACTED_ZIP]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.HIPAA],
                priority=4
            ),
            RedactionRule(
                name="street_address",
                pattern=r'\b\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b',
                replacement="[REDACTED_ADDRESS]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.HIPAA],
                priority=4
            )
        ]
        
        # Date and Time Rules (High sensitivity)
        datetime_rules = [
            RedactionRule(
                name="date_of_birth",
                pattern=r'\b(?:DOB|Date of Birth|Born):?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                replacement="[REDACTED_DOB]",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.HIPAA],
                priority=8
            ),
            RedactionRule(
                name="precise_timestamp",
                pattern=r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})',
                replacement="[REDACTED_TIMESTAMP]",
                compliance_standards=[ComplianceStandard.GDPR],
                priority=2
            )
        ]
        
        # Government IDs and Numbers
        government_rules = [
            RedactionRule(
                name="passport_number",
                pattern=r'\b[A-Z]{1,2}\d{6,9}\b',
                replacement="[REDACTED_PASSPORT]",
                compliance_standards=[ComplianceStandard.GDPR],
                priority=7
            ),
            RedactionRule(
                name="drivers_license",
                pattern=r'\b[A-Z]{1,2}[-\s]?\d{6,8}\b',
                replacement="[REDACTED_LICENSE]",
                compliance_standards=[ComplianceStandard.GDPR],
                priority=6
            )
        ]
        
        # Combine all rules based on redaction level
        all_rules = financial_rules + personal_rules
        
        if self.level in [RedactionLevel.MEDIUM, RedactionLevel.HIGH]:
            all_rules.extend(location_rules)
        
        if self.level == RedactionLevel.HIGH:
            all_rules.extend(datetime_rules + government_rules)
        
        # Sort by priority (higher first)
        self.rules = sorted(all_rules, key=lambda x: x.priority, reverse=True)
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        for rule in self.rules + self.custom_rules:
            if rule.enabled:
                try:
                    self._compiled_patterns[rule.name] = re.compile(rule.pattern, re.IGNORECASE)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern for rule '{rule.name}': {e}")
    
    def add_custom_rule(self, rule: RedactionRule):
        """Add custom redaction rule"""
        self.custom_rules.append(rule)
        try:
            self._compiled_patterns[rule.name] = re.compile(rule.pattern, re.IGNORECASE)
            logger.info(f"Added custom rule: {rule.name}")
        except re.error as e:
            logger.error(f"Invalid regex pattern for custom rule '{rule.name}': {e}")
    
    def remove_rule(self, rule_name: str):
        """Remove a redaction rule"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        self.custom_rules = [r for r in self.custom_rules if r.name != rule_name]
        if rule_name in self._compiled_patterns:
            del self._compiled_patterns[rule_name]
        logger.info(f"Removed rule: {rule_name}")
    
    def enable_rule(self, rule_name: str, enabled: bool = True):
        """Enable or disable a specific rule"""
        for rule in self.rules + self.custom_rules:
            if rule.name == rule_name:
                rule.enabled = enabled
                if enabled and rule_name not in self._compiled_patterns:
                    self._compiled_patterns[rule_name] = re.compile(rule.pattern, re.IGNORECASE)
                elif not enabled and rule_name in self._compiled_patterns:
                    del self._compiled_patterns[rule_name]
                logger.info(f"Rule '{rule_name}' {'enabled' if enabled else 'disabled'}")
                return
        logger.warning(f"Rule '{rule_name}' not found")
    
    def _calculate_risk_score(self, original_text: str, redactions: Dict[str, int]) -> float:
        """Calculate privacy risk score based on redactions made"""
        risk_weights = {
            "credit_card": 10.0,
            "ssn": 10.0,
            "bank_account": 9.0,
            "passport": 8.0,
            "phone": 5.0,
            "email": 4.0,
            "address": 6.0,
            "large_amounts": 3.0
        }
        
        total_risk = 0.0
        text_length = len(original_text)
        
        for rule_name, count in redactions.items():
            # Get base risk from rule type
            base_risk = 0.0
            for risk_type, weight in risk_weights.items():
                if risk_type in rule_name.lower():
                    base_risk = weight
                    break
            
            # Risk increases with frequency
            frequency_multiplier = min(count / 10.0, 2.0)  # Cap at 2x
            total_risk += base_risk * frequency_multiplier
        
        # Normalize by text length (longer texts naturally have more risks)
        normalized_risk = total_risk / max(text_length / 100, 1.0)
        
        return min(normalized_risk, 100.0)  # Cap at 100
    
    def _check_compliance_violations(self, text: str) -> List[str]:
        """Check for potential compliance violations"""
        violations = []
        
        # Check for unredacted sensitive patterns
        violation_patterns = {
            ComplianceStandard.PCI_DSS: [
                (r'\b4\d{15}\b', "Unredacted Visa card number"),
                (r'\b5[1-5]\d{14}\b', "Unredacted Mastercard number"),
            ],
            ComplianceStandard.GDPR: [
                (r'\b\w+@\w+\.\w+\b', "Potential unredacted email"),
                (r'\b\d{3}-\d{2}-\d{4}\b', "Potential unredacted SSN"),
            ],
            ComplianceStandard.HIPAA: [
                (r'\bDOB:?\s*\d+[/\-]\d+[/\-]\d+', "Potential date of birth"),
            ]
        }
        
        for standard, patterns in violation_patterns.items():
            for pattern, description in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append(f"{standard.value.upper()}: {description}")
        
        return violations
    
    def redact_text(self, text: str, preserve_structure: bool = True) -> RedactionResult:
        """
        Advanced text redaction with comprehensive analysis
        
        Args:
            text: Input text to redact
            preserve_structure: Whether to preserve text structure
            
        Returns:
            RedactionResult with detailed analysis
        """
        import time
        start_time = time.time()
        
        if not text or not isinstance(text, str):
            return RedactionResult(
                original_text=text or "",
                redacted_text=text or "",
                redactions_made={},
                risk_score=0.0,
                compliance_violations=[],
                processing_time_ms=0.0
            )
        
        redacted_text = text
        redactions_made = {}
        
        # Apply all enabled rules in priority order
        all_rules = sorted(
            [r for r in self.rules + self.custom_rules if r.enabled],
            key=lambda x: x.priority,
            reverse=True
        )
        
        for rule in all_rules:
            if rule.name in self._compiled_patterns:
                pattern = self._compiled_patterns[rule.name]
                matches = pattern.findall(redacted_text)
                
                if matches:
                    redactions_made[rule.name] = len(matches)
                    
                    if rule.preserve_format and rule.name == "credit_card_full":
                        # Preserve card format: 4*** **** **** 1234
                        def format_card(match):
                            card = re.sub(r'[-\s]', '', match.group(0))
                            return f"{card[:1]}*** **** **** {card[-4:]}"
                        redacted_text = pattern.sub(format_card, redacted_text)
                    else:
                        redacted_text = pattern.sub(rule.replacement, redacted_text)
                    
                    # Update performance stats
                    self.performance_stats["rules_applied"][rule.name] = \
                        self.performance_stats["rules_applied"].get(rule.name, 0) + len(matches)
        
        # Calculate metrics
        risk_score = self._calculate_risk_score(text, redactions_made)
        compliance_violations = self._check_compliance_violations(redacted_text)
        processing_time = (time.time() - start_time) * 1000
        
        # Update global stats
        self.performance_stats["total_redactions"] += sum(redactions_made.values())
        self.performance_stats["total_processing_time"] += processing_time
        
        return RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            redactions_made=redactions_made,
            risk_score=risk_score,
            compliance_violations=compliance_violations,
            processing_time_ms=processing_time
        )
    
    def batch_redact(self, texts: List[str]) -> List[RedactionResult]:
        """Batch redaction for multiple texts"""
        return [self.redact_text(text) for text in texts]
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics"""
        return {
            **self.performance_stats,
            "total_rules": len(self.rules) + len(self.custom_rules),
            "enabled_rules": len([r for r in self.rules + self.custom_rules if r.enabled]),
            "redaction_level": self.level.value
        }
    
    def export_config(self, filepath: str):
        """Export redaction configuration"""
        config = {
            "level": self.level.value,
            "rules": [
                {
                    "name": rule.name,
                    "pattern": rule.pattern,
                    "replacement": rule.replacement,
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                    "compliance_standards": [s.value for s in rule.compliance_standards]
                }
                for rule in self.rules + self.custom_rules
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration exported to {filepath}")
    
    def import_config(self, filepath: str):
        """Import redaction configuration"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            self.level = RedactionLevel(config.get("level", "medium"))
            self.custom_rules = []
            
            for rule_config in config.get("rules", []):
                rule = RedactionRule(
                    name=rule_config["name"],
                    pattern=rule_config["pattern"],
                    replacement=rule_config["replacement"],
                    enabled=rule_config.get("enabled", True),
                    priority=rule_config.get("priority", 0),
                    compliance_standards=[
                        ComplianceStandard(s) for s in rule_config.get("compliance_standards", [])
                    ]
                )
                self.custom_rules.append(rule)
            
            self._compile_patterns()
            logger.info(f"Configuration imported from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")

# Global redaction engine instance
_redaction_engine = AdvancedRedactionEngine()

@lru_cache(maxsize=1000)
def redact_sensitive(text: str) -> str:
    """
    Cached redaction function for backward compatibility
    
    Args:
        text: Input text to redact
        
    Returns:
        Redacted text string
    """
    if not text:
        return text
    
    result = _redaction_engine.redact_text(text)
    return result.redacted_text

def redact_with_analysis(text: str, level: RedactionLevel = RedactionLevel.MEDIUM) -> RedactionResult:
    """
    Advanced redaction with detailed analysis
    
    Args:
        text: Input text to redact
        level: Redaction security level
        
    Returns:
        Detailed redaction result
    """
    engine = AdvancedRedactionEngine(level)
    return engine.redact_text(text)

def create_custom_redactor(
    rules: List[RedactionRule], 
    level: RedactionLevel = RedactionLevel.CUSTOM
) -> AdvancedRedactionEngine:
    """
    Create custom redaction engine with specific rules
    
    Args:
        rules: List of custom redaction rules
        level: Redaction security level
        
    Returns:
        Configured redaction engine
    """
    engine = AdvancedRedactionEngine(level)
    for rule in rules:
        engine.add_custom_rule(rule)
    return engine

def validate_redaction_quality(original: str, redacted: str) -> Dict[str, any]:
    """
    Validate redaction quality and completeness
    
    Args:
        original: Original text
        redacted: Redacted text
        
    Returns:
        Quality assessment dictionary
    """
    # Check for common patterns that should be redacted
    sensitive_patterns = [
        (r'\b4\d{15}\b', "Credit card numbers"),
        (r'\b\d{3}-\d{2}-\d{4}\b', "Social Security numbers"),
        (r'\b\w+@\w+\.\w+\b', "Email addresses"),
        (r'\b\d{3}-\d{3}-\d{4}\b', "Phone numbers")
    ]
    
    issues = []
    for pattern, description in sensitive_patterns:
        if re.search(pattern, redacted):
            issues.append(f"Potential unredacted {description.lower()}")
    
    reduction_ratio = 1 - (len(redacted) / len(original)) if original else 0
    
    return {
        "quality_score": max(0, 100 - len(issues) * 25),  # Penalize issues
        "issues_found": issues,
        "text_reduction_ratio": reduction_ratio,
        "redaction_effective": len(issues) == 0,
        "original_length": len(original),
        "redacted_length": len(redacted)
    }

# Compliance-specific redactors
def create_pci_dss_redactor() -> AdvancedRedactionEngine:
    """Create PCI DSS compliant redactor"""
    engine = AdvancedRedactionEngine(RedactionLevel.HIGH)
    # Enable only PCI DSS relevant rules
    for rule in engine.rules:
        rule.enabled = ComplianceStandard.PCI_DSS in rule.compliance_standards
    engine._compile_patterns()
    return engine

def create_gdpr_redactor() -> AdvancedRedactionEngine:
    """Create GDPR compliant redactor"""
    engine = AdvancedRedactionEngine(RedactionLevel.HIGH)
    # Enable only GDPR relevant rules
    for rule in engine.rules:
        rule.enabled = ComplianceStandard.GDPR in rule.compliance_standards
    engine._compile_patterns()
    return engine

if __name__ == "__main__":
    # Comprehensive testing
    print("🔒 Testing Advanced Redaction Engine...")
    
    test_texts = [
        "My credit card 4532-1234-5678-9012 was charged $1500.00",
        "Contact me at john.doe@email.com or call (555) 123-4567",
        "SSN: 123-45-6789, Account: 1234567890",
        "Address: 123 Main Street, Anytown 12345"
    ]
    
    # Test different security levels
    for level in [RedactionLevel.LOW, RedactionLevel.MEDIUM, RedactionLevel.HIGH]:
        print(f"\n📊 Testing {level.value.upper()} security level:")
        engine = AdvancedRedactionEngine(level)
        
        for text in test_texts:
            result = engine.redact_text(text)
            print(f"  Original: {text}")
            print(f"  Redacted: {result.redacted_text}")
            print(f"  Risk Score: {result.risk_score:.1f}")
            if result.compliance_violations:
                print(f"  Violations: {result.compliance_violations}")
            print()
    
    # Test performance
    print("⚡ Performance Statistics:")
    stats = _redaction_engine.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
