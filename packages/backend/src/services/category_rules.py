"""
Category Rules Service for rule-based transaction categorization.
Supports keyword matching, regex patterns, merchant rules, and amount-based rules.
"""

import re
import json
import logging
from typing import List, Dict, Tuple, Optional, Any, Union
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..database.models import Transaction, Category, CategorizationRule
from ..config import settings

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of categorization rules."""
    MERCHANT = "merchant"
    KEYWORD = "keyword"
    AMOUNT = "amount"
    REGEX = "regex"
    COMPOUND = "compound"
    ML_ASSISTED = "ml_assisted"


class PatternType(Enum):
    """Types of pattern matching."""
    CONTAINS = "contains"
    EXACT = "exact"
    REGEX = "regex"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    FUZZY = "fuzzy"


@dataclass
class RuleMatch:
    """Result of a rule match."""
    rule_id: str
    category_name: str
    confidence: float
    priority: int
    rule_name: str
    match_field: str
    matched_text: str


@dataclass
class RuleCondition:
    """Condition for rule application."""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, contains, regex
    value: Any
    case_sensitive: bool = False


class CategoryRulesService:
    """
    Service for managing and applying categorization rules.
    Supports multiple rule types, priorities, and complex conditions.
    """

    def __init__(self):
        """Initialize the category rules service."""
        self.confidence_threshold = 0.7
        self.default_rules = self._load_default_rules()

    def _load_default_rules(self) -> List[Dict[str, Any]]:
        """Load default system rules."""
        return [
            # Food & Dining
            {
                "name": "Food & Dining - Major Chains",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(starbucks|mcdonald|subway|pizza hut|domino|taco bell|kfc|burger king)",
                "pattern_type": PatternType.REGEX,
                "category": "Food & Dining",
                "confidence": 0.95,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },
            {
                "name": "Food & Dining - Delivery Services",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(uber.*eats|doordash|grubhub|postmates|seamless|caviar)",
                "pattern_type": PatternType.REGEX,
                "category": "Food & Dining",
                "confidence": 0.90,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },
            {
                "name": "Food & Dining - General",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(restaurant|cafe|coffee|food|dining|eat|bakery|deli)",
                "pattern_type": PatternType.REGEX,
                "category": "Food & Dining",
                "confidence": 0.80,
                "priority": 3,
                "match_fields": ["name", "merchant_name", "description"]
            },

            # Transportation
            {
                "name": "Transportation - Rideshare",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(uber|lyft|taxi|cab|rideshare)",
                "pattern_type": PatternType.REGEX,
                "category": "Transportation",
                "confidence": 0.95,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },
            {
                "name": "Transportation - Gas Stations",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(shell|exxon|chevron|bp|mobil|citgo|texaco|sunoco|gas|fuel)",
                "pattern_type": PatternType.REGEX,
                "category": "Transportation",
                "confidence": 0.90,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },
            {
                "name": "Transportation - Public Transit",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(metro|transit|bus|train|subway|bart|mta|parking)",
                "pattern_type": PatternType.REGEX,
                "category": "Transportation",
                "confidence": 0.85,
                "priority": 2,
                "match_fields": ["name", "merchant_name"]
            },

            # Shopping
            {
                "name": "Shopping - Major Retailers",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(amazon|walmart|target|costco|best buy|home depot|lowes)",
                "pattern_type": PatternType.REGEX,
                "category": "Shopping",
                "confidence": 0.95,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },
            {
                "name": "Shopping - Online",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(ebay|etsy|\.com|online.*store|paypal.*.*)",
                "pattern_type": PatternType.REGEX,
                "category": "Shopping",
                "confidence": 0.75,
                "priority": 3,
                "match_fields": ["name", "merchant_name"]
            },

            # Bills & Utilities
            {
                "name": "Bills & Utilities - Utilities",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(electric|electricity|gas.*utility|water|sewer|internet|cable|phone)",
                "pattern_type": PatternType.REGEX,
                "category": "Bills & Utilities",
                "confidence": 0.95,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },
            {
                "name": "Bills & Utilities - Telecom",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(verizon|at&t|t-mobile|sprint|comcast|xfinity|spectrum)",
                "pattern_type": PatternType.REGEX,
                "category": "Bills & Utilities",
                "confidence": 0.90,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },

            # Entertainment
            {
                "name": "Entertainment - Streaming",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(netflix|spotify|hulu|disney|amazon.*prime|apple.*music|youtube.*premium)",
                "pattern_type": PatternType.REGEX,
                "category": "Entertainment",
                "confidence": 0.95,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },
            {
                "name": "Entertainment - Gaming",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(steam|playstation|xbox|nintendo|game|gaming)",
                "pattern_type": PatternType.REGEX,
                "category": "Entertainment",
                "confidence": 0.85,
                "priority": 2,
                "match_fields": ["name", "merchant_name"]
            },

            # Healthcare
            {
                "name": "Healthcare - Medical",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(hospital|clinic|doctor|medical|pharmacy|cvs|walgreens|rite aid)",
                "pattern_type": PatternType.REGEX,
                "category": "Healthcare",
                "confidence": 0.90,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },

            # Income
            {
                "name": "Income - Payroll",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(salary|payroll|direct.*deposit|income|wage|payment.*from)",
                "pattern_type": PatternType.REGEX,
                "category": "Income",
                "confidence": 0.95,
                "priority": 1,
                "match_fields": ["name", "description"],
                "conditions": [
                    {"field": "amount", "operator": "gt", "value": 0}
                ]
            },

            # Transfer
            {
                "name": "Transfer - P2P",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(transfer|zelle|venmo|paypal|cash.*app|wire|p2p)",
                "pattern_type": PatternType.REGEX,
                "category": "Transfer",
                "confidence": 0.90,
                "priority": 1,
                "match_fields": ["name", "merchant_name"]
            },

            # Fees & Charges
            {
                "name": "Fees & Charges",
                "rule_type": RuleType.KEYWORD,
                "pattern": r"(?i)(fee|charge|penalty|overdraft|interest.*charged|finance.*charge)",
                "pattern_type": PatternType.REGEX,
                "category": "Fees & Charges",
                "confidence": 0.95,
                "priority": 1,
                "match_fields": ["name", "description"]
            },

            # Amount-based rules
            {
                "name": "Large Income Deposits",
                "rule_type": RuleType.AMOUNT,
                "category": "Income",
                "confidence": 0.80,
                "priority": 2,
                "conditions": [
                    {"field": "amount", "operator": "gte", "value": 1000},
                    {"field": "transaction_type", "operator": "eq", "value": "credit"},
                    {"field": "name", "operator": "contains", "value": "deposit", "case_sensitive": False}
                ]
            },

            # Compound rules (multiple conditions)
            {
                "name": "ATM Withdrawals",
                "rule_type": RuleType.COMPOUND,
                "category": "Transfer",
                "confidence": 0.85,
                "priority": 2,
                "conditions": [
                    {"field": "name", "operator": "contains", "value": "atm", "case_sensitive": False},
                    {"field": "amount", "operator": "gt", "value": 0}
                ]
            }
        ]

    def apply_rules(
        self,
        transaction: Transaction,
        db: Session,
        user_id: Optional[str] = None
    ) -> List[RuleMatch]:
        """
        Apply all applicable rules to a transaction.

        Args:
            transaction: Transaction to categorize
            db: Database session
            user_id: User ID for user-specific rules

        Returns:
            List of rule matches sorted by priority and confidence
        """
        matches = []

        # Apply user-specific rules first
        if user_id:
            user_rules = self._get_user_rules(db, user_id)
            for rule in user_rules:
                match = self._apply_single_rule(transaction, rule)
                if match:
                    matches.append(match)

        # Apply default system rules
        for rule_config in self.default_rules:
            match = self._apply_default_rule(transaction, rule_config)
            if match:
                matches.append(match)

        # Sort by priority (lower is better) then confidence (higher is better)
        matches.sort(key=lambda x: (x.priority, -x.confidence))

        return matches

    def _get_user_rules(self, db: Session, user_id: str) -> List[CategorizationRule]:
        """Get active user-specific rules."""
        return db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True
        ).order_by(
            CategorizationRule.priority,
            CategorizationRule.created_at
        ).all()

    def _apply_single_rule(self, transaction: Transaction, rule: CategorizationRule) -> Optional[RuleMatch]:
        """Apply a single database rule to a transaction."""
        try:
            # Check if rule conditions are met
            if not self._check_rule_conditions(transaction, rule.conditions or {}):
                return None

            # Apply pattern matching
            matched_field, matched_text = self._apply_pattern_matching(
                transaction,
                rule.pattern,
                PatternType(rule.pattern_type),
                rule.match_fields or ["name", "merchant_name"]
            )

            if matched_field:
                # Update rule statistics
                rule.increment_match_count()

                return RuleMatch(
                    rule_id=str(rule.id),
                    category_name=rule.category.name if rule.category else "Unknown",
                    confidence=0.9,  # Database rules get high confidence
                    priority=rule.priority,
                    rule_name=rule.name,
                    match_field=matched_field,
                    matched_text=matched_text
                )

        except Exception as e:
            logger.error(f"Error applying rule {rule.id}: {e}")

        return None

    def _apply_default_rule(self, transaction: Transaction, rule_config: Dict[str, Any]) -> Optional[RuleMatch]:
        """Apply a default rule configuration to a transaction."""
        try:
            # Check conditions if any
            if "conditions" in rule_config:
                if not self._check_conditions(transaction, rule_config["conditions"]):
                    return None

            # Apply pattern matching
            matched_field, matched_text = self._apply_pattern_matching(
                transaction,
                rule_config["pattern"],
                rule_config["pattern_type"],
                rule_config.get("match_fields", ["name", "merchant_name"])
            )

            if matched_field:
                return RuleMatch(
                    rule_id=f"default_{rule_config['name'].lower().replace(' ', '_')}",
                    category_name=rule_config["category"],
                    confidence=rule_config["confidence"],
                    priority=rule_config["priority"],
                    rule_name=rule_config["name"],
                    match_field=matched_field,
                    matched_text=matched_text
                )

        except Exception as e:
            logger.error(f"Error applying default rule {rule_config['name']}: {e}")

        return None

    def _apply_pattern_matching(
        self,
        transaction: Transaction,
        pattern: str,
        pattern_type: PatternType,
        match_fields: List[str]
    ) -> Tuple[Optional[str], str]:
        """Apply pattern matching to transaction fields."""

        for field_name in match_fields:
            field_value = self._get_transaction_field_value(transaction, field_name)
            if not field_value:
                continue

            field_value = str(field_value)

            # Apply different pattern matching types
            is_match = False

            if pattern_type == PatternType.CONTAINS:
                is_match = pattern.lower() in field_value.lower()
            elif pattern_type == PatternType.EXACT:
                is_match = pattern.lower() == field_value.lower()
            elif pattern_type == PatternType.REGEX:
                is_match = bool(re.search(pattern, field_value))
            elif pattern_type == PatternType.STARTS_WITH:
                is_match = field_value.lower().startswith(pattern.lower())
            elif pattern_type == PatternType.ENDS_WITH:
                is_match = field_value.lower().endswith(pattern.lower())
            elif pattern_type == PatternType.FUZZY:
                # Simple fuzzy matching using edit distance (could be enhanced)
                is_match = self._fuzzy_match(pattern, field_value)

            if is_match:
                return field_name, field_value

        return None, ""

    def _get_transaction_field_value(self, transaction: Transaction, field_name: str) -> Optional[str]:
        """Get field value from transaction object."""
        field_mapping = {
            "name": transaction.name,
            "merchant_name": transaction.merchant_name,
            "description": transaction.description,
            "amount": transaction.amount,
            "transaction_type": transaction.transaction_type,
            "payment_method": transaction.payment_method,
            "payment_channel": transaction.payment_channel,
        }

        return field_mapping.get(field_name)

    def _check_rule_conditions(self, transaction: Transaction, conditions: Dict[str, Any]) -> bool:
        """Check if transaction meets rule conditions."""
        if not conditions:
            return True

        try:
            # Parse conditions (could be JSON string or dict)
            if isinstance(conditions, str):
                conditions = json.loads(conditions)

            if isinstance(conditions, list):
                # All conditions must be true (AND logic)
                return all(self._check_single_condition(transaction, cond) for cond in conditions)
            else:
                # Single condition
                return self._check_single_condition(transaction, conditions)

        except Exception as e:
            logger.error(f"Error checking rule conditions: {e}")
            return False

    def _check_conditions(self, transaction: Transaction, conditions: List[Dict[str, Any]]) -> bool:
        """Check conditions for default rules."""
        return all(self._check_single_condition(transaction, cond) for cond in conditions)

    def _check_single_condition(self, transaction: Transaction, condition: Dict[str, Any]) -> bool:
        """Check a single condition against transaction."""
        field = condition["field"]
        operator = condition["operator"]
        expected_value = condition["value"]
        case_sensitive = condition.get("case_sensitive", False)

        # Get actual value from transaction
        actual_value = self._get_transaction_field_value(transaction, field)

        if actual_value is None:
            return False

        # Convert to appropriate types
        if field == "amount":
            actual_value = float(actual_value)
            expected_value = float(expected_value)
        elif not case_sensitive and isinstance(actual_value, str):
            actual_value = actual_value.lower()
            if isinstance(expected_value, str):
                expected_value = expected_value.lower()

        # Apply operator
        if operator == "eq":
            return actual_value == expected_value
        elif operator == "ne":
            return actual_value != expected_value
        elif operator == "gt":
            return actual_value > expected_value
        elif operator == "lt":
            return actual_value < expected_value
        elif operator == "gte":
            return actual_value >= expected_value
        elif operator == "lte":
            return actual_value <= expected_value
        elif operator == "in":
            return actual_value in expected_value
        elif operator == "not_in":
            return actual_value not in expected_value
        elif operator == "contains":
            return expected_value in str(actual_value)
        elif operator == "regex":
            return bool(re.search(expected_value, str(actual_value)))
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    def _fuzzy_match(self, pattern: str, text: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy string matching."""
        # This is a basic implementation - could be enhanced with proper fuzzy matching
        pattern = pattern.lower()
        text = text.lower()

        # Check if pattern is substantially contained in text
        if len(pattern) <= 3:
            return pattern in text

        # For longer patterns, check if most characters are present
        pattern_chars = set(pattern)
        text_chars = set(text)
        overlap = len(pattern_chars.intersection(text_chars))
        similarity = overlap / len(pattern_chars)

        return similarity >= threshold

    def create_user_rule(
        self,
        db: Session,
        user_id: str,
        rule_data: Dict[str, Any]
    ) -> CategorizationRule:
        """Create a new user-specific categorization rule."""

        # Get or create category
        category = db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == rule_data["category_name"]
        ).first()

        if not category:
            # Create new category
            category = Category(
                user_id=user_id,
                name=rule_data["category_name"],
                category_type="expense",  # Default
                is_system_category=False
            )
            db.add(category)
            db.flush()  # Get the ID

        # Create rule
        rule = CategorizationRule(
            user_id=user_id,
            category_id=category.id,
            name=rule_data["name"],
            description=rule_data.get("description"),
            rule_type=rule_data["rule_type"],
            pattern=rule_data["pattern"],
            pattern_type=rule_data.get("pattern_type", "contains"),
            case_sensitive=rule_data.get("case_sensitive", False),
            match_fields=rule_data.get("match_fields", ["name", "merchant_name"]),
            conditions=rule_data.get("conditions"),
            priority=rule_data.get("priority", 100),
            auto_apply=rule_data.get("auto_apply", True),
            requires_approval=rule_data.get("requires_approval", False)
        )

        db.add(rule)
        db.commit()

        logger.info(f"Created rule '{rule.name}' for user {user_id}")
        return rule

    def update_rule_accuracy(
        self,
        db: Session,
        rule_id: str,
        was_correct: bool
    ) -> Optional[CategorizationRule]:
        """Update rule accuracy based on feedback."""

        rule = db.query(CategorizationRule).filter(
            CategorizationRule.id == rule_id
        ).first()

        if rule:
            feedback_score = 10 if was_correct else -10
            rule.update_accuracy(feedback_score)
            db.commit()

            logger.info(f"Updated accuracy for rule '{rule.name}': {rule.accuracy_score}")

        return rule

    def get_rule_statistics(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's rules."""

        rules = db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id
        ).all()

        stats = {
            "total_rules": len(rules),
            "active_rules": sum(1 for r in rules if r.is_active),
            "rules_by_type": {},
            "top_performing_rules": [],
            "rules_needing_review": []
        }

        # Group by type
        for rule in rules:
            rule_type = rule.rule_type
            if rule_type not in stats["rules_by_type"]:
                stats["rules_by_type"][rule_type] = 0
            stats["rules_by_type"][rule_type] += 1

        # Sort by performance
        performing_rules = [r for r in rules if r.match_count > 0]
        performing_rules.sort(key=lambda x: x.accuracy_score, reverse=True)

        stats["top_performing_rules"] = [
            {
                "name": r.name,
                "accuracy_score": r.accuracy_score,
                "match_count": r.match_count,
                "category": r.category.name if r.category else "Unknown"
            }
            for r in performing_rules[:5]
        ]

        # Rules needing review
        stats["rules_needing_review"] = [
            {
                "name": r.name,
                "accuracy_score": r.accuracy_score,
                "match_count": r.match_count,
                "reason": "Poor accuracy" if r.accuracy_score < -50 else "Low usage"
            }
            for r in rules if r.needs_review
        ]

        return stats

    def get_best_rule_match(self, transaction: Transaction, db: Session, user_id: Optional[str] = None) -> Optional[RuleMatch]:
        """Get the best rule match for a transaction."""
        matches = self.apply_rules(transaction, db, user_id)

        if matches:
            # Return highest priority, highest confidence match
            return matches[0]

        return None


# Singleton instance
category_rules_service = CategoryRulesService()