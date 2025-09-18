#!/usr/bin/env python3
"""
Comprehensive data seeding script for the transaction categorization system.
Creates standard financial categories, rules, and sample transactions for testing.
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from uuid import uuid4
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base
from src.database.models import (
    User, Account, Transaction, Category, Institution, PlaidItem
)
from src.config import settings
from src.utils.security import hash_password

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CategorySeeder:
    """
    Comprehensive seeding for the categorization system.
    Creates standard categories, rules, and sample data.
    """

    def __init__(self, database_url: str = None):
        """Initialize seeder with database connection."""
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_standard_categories(self, db: Session, user_id: str) -> List[Category]:
        """Create comprehensive standard financial categories with rules."""
        logger.info("Creating standard financial categories...")

        categories_data = [
            # Income Categories
            {
                "name": "Salary & Wages",
                "parent_category": "Income",
                "description": "Regular employment income including salary, wages, and bonuses",
                "color": "#4CAF50",
                "icon": "work",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "salary",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "payroll",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "wages",
                        "confidence": 0.9
                    },
                    {
                        "type": "amount_range",
                        "field": "amount",
                        "operator": "greater_than",
                        "value": "1000",
                        "confidence": 0.7
                    }
                ]
            },
            {
                "name": "Freelance & Consulting",
                "parent_category": "Income",
                "description": "Income from freelance work, consulting, and contract work",
                "color": "#66BB6A",
                "icon": "business_center",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "freelance",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "consulting",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "contract",
                        "confidence": 0.8
                    }
                ]
            },
            {
                "name": "Investment Income",
                "parent_category": "Income",
                "description": "Dividends, interest, capital gains, and investment returns",
                "color": "#81C784",
                "icon": "trending_up",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "dividend",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "interest",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "capital gain",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Refunds & Reimbursements",
                "parent_category": "Income",
                "description": "Tax refunds, expense reimbursements, and returns",
                "color": "#A5D6A7",
                "icon": "receipt_long",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "refund",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "reimbursement",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "return",
                        "confidence": 0.8
                    }
                ]
            },

            # Food & Dining Categories
            {
                "name": "Restaurants",
                "parent_category": "Food & Dining",
                "description": "Dining out, restaurants, and food delivery",
                "color": "#FF5722",
                "icon": "restaurant",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "restaurant",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "dining",
                        "confidence": 0.85
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "uber eats",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "doordash",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "grubhub",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Fast Food",
                "parent_category": "Food & Dining",
                "description": "Quick service restaurants and fast food chains",
                "color": "#F44336",
                "icon": "fastfood",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "mcdonald",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "burger king",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "subway",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "taco bell",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "kfc",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Coffee & Cafes",
                "parent_category": "Food & Dining",
                "description": "Coffee shops, cafes, and beverage purchases",
                "color": "#8D6E63",
                "icon": "local_cafe",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "starbucks",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "coffee",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "cafe",
                        "confidence": 0.85
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "espresso",
                        "confidence": 0.9
                    }
                ]
            },
            {
                "name": "Groceries",
                "parent_category": "Food & Dining",
                "description": "Grocery stores and food shopping",
                "color": "#FF7043",
                "icon": "shopping_cart",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "grocery",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "supermarket",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "whole foods",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "kroger",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "safeway",
                        "confidence": 0.95
                    }
                ]
            },

            # Transportation Categories
            {
                "name": "Gas & Fuel",
                "parent_category": "Transportation",
                "description": "Gasoline, diesel, and vehicle fuel",
                "color": "#2196F3",
                "icon": "local_gas_station",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "shell",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "exxon",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "chevron",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "bp",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "gas station",
                        "confidence": 0.9
                    }
                ]
            },
            {
                "name": "Public Transportation",
                "parent_category": "Transportation",
                "description": "Bus, train, subway, and public transit",
                "color": "#1976D2",
                "icon": "train",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "metro",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "transit",
                        "confidence": 0.85
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "subway",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "bus pass",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Rideshare & Taxi",
                "parent_category": "Transportation",
                "description": "Uber, Lyft, taxis, and rideshare services",
                "color": "#1565C0",
                "icon": "local_taxi",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "uber",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "lyft",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "taxi",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "rideshare",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Parking",
                "parent_category": "Transportation",
                "description": "Parking fees, meters, and garage costs",
                "color": "#0D47A1",
                "icon": "local_parking",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "parking",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "parkwhiz",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "meter",
                        "confidence": 0.8
                    }
                ]
            },

            # Shopping Categories
            {
                "name": "Online Shopping",
                "parent_category": "Shopping",
                "description": "Amazon, online retailers, and e-commerce",
                "color": "#9C27B0",
                "icon": "shopping_basket",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "amazon",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "ebay",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "etsy",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "online",
                        "confidence": 0.7
                    }
                ]
            },
            {
                "name": "Department Stores",
                "parent_category": "Shopping",
                "description": "Target, Walmart, and general retail stores",
                "color": "#8E24AA",
                "icon": "store",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "target",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "walmart",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "costco",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "sams club",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Clothing & Accessories",
                "parent_category": "Shopping",
                "description": "Clothing stores, fashion, and accessories",
                "color": "#7B1FA2",
                "icon": "checkroom",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "clothing",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "fashion",
                        "confidence": 0.85
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "h&m",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "zara",
                        "confidence": 0.95
                    }
                ]
            },

            # Bills & Utilities Categories
            {
                "name": "Utilities",
                "parent_category": "Bills & Utilities",
                "description": "Electric, gas, water, and utility bills",
                "color": "#FF9800",
                "icon": "power",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "electric",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "utility",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "water bill",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "gas bill",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Internet & Cable",
                "parent_category": "Bills & Utilities",
                "description": "Internet, cable TV, and telecommunications",
                "color": "#F57C00",
                "icon": "wifi",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "comcast",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "xfinity",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "spectrum",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "internet",
                        "confidence": 0.9
                    }
                ]
            },
            {
                "name": "Phone",
                "parent_category": "Bills & Utilities",
                "description": "Mobile and landline phone services",
                "color": "#EF6C00",
                "icon": "phone",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "verizon",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "at&t",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "t-mobile",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "wireless",
                        "confidence": 0.85
                    }
                ]
            },
            {
                "name": "Insurance",
                "parent_category": "Bills & Utilities",
                "description": "Health, auto, home, and other insurance premiums",
                "color": "#E65100",
                "icon": "security",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "insurance",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "premium",
                        "confidence": 0.85
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "geico",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "state farm",
                        "confidence": 0.95
                    }
                ]
            },

            # Healthcare Categories
            {
                "name": "Medical & Dental",
                "parent_category": "Healthcare",
                "description": "Doctor visits, dental care, and medical services",
                "color": "#4CAF50",
                "icon": "local_hospital",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "medical",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "doctor",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "dental",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "clinic",
                        "confidence": 0.85
                    }
                ]
            },
            {
                "name": "Pharmacy",
                "parent_category": "Healthcare",
                "description": "Prescription medications and pharmacy purchases",
                "color": "#66BB6A",
                "icon": "local_pharmacy",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "cvs",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "walgreens",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "pharmacy",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "prescription",
                        "confidence": 0.95
                    }
                ]
            },

            # Entertainment Categories
            {
                "name": "Streaming Services",
                "parent_category": "Entertainment",
                "description": "Netflix, Spotify, and subscription services",
                "color": "#E91E63",
                "icon": "play_circle",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "netflix",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "spotify",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "hulu",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "disney",
                        "confidence": 0.9
                    }
                ]
            },
            {
                "name": "Movies & Events",
                "parent_category": "Entertainment",
                "description": "Movie theaters, concerts, and live events",
                "color": "#C2185B",
                "icon": "movie",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "amc",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "movie",
                        "confidence": 0.85
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "theater",
                        "confidence": 0.8
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "concert",
                        "confidence": 0.9
                    }
                ]
            },

            # Transfer Categories
            {
                "name": "Bank Transfers",
                "parent_category": "Transfer",
                "description": "Internal transfers and bank-to-bank movements",
                "color": "#607D8B",
                "icon": "swap_horiz",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "transfer",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "wire",
                        "confidence": 0.85
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "ach",
                        "confidence": 0.9
                    }
                ]
            },
            {
                "name": "P2P Payments",
                "parent_category": "Transfer",
                "description": "Venmo, PayPal, and person-to-person payments",
                "color": "#546E7A",
                "icon": "send",
                "is_system": True,
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "venmo",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "paypal",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "zelle",
                        "confidence": 0.95
                    },
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "cash app",
                        "confidence": 0.95
                    }
                ]
            }
        ]

        categories = []
        for cat_data in categories_data:
            category = Category(
                user_id=user_id,
                name=cat_data["name"],
                parent_category=cat_data["parent_category"],
                description=cat_data["description"],
                color=cat_data["color"],
                icon=cat_data["icon"],
                rules=cat_data["rules"],
                is_system=cat_data.get("is_system", True),
                is_active=True
            )
            db.add(category)
            categories.append(category)

        db.commit()
        logger.info(f"Created {len(categories)} standard categories")
        return categories

    def create_sample_transactions(self, db: Session, account_id: str, categories: List[Category]) -> List[Transaction]:
        """Create diverse sample transactions for testing categorization."""
        logger.info("Creating sample transactions...")

        # Create realistic transaction patterns
        transactions_data = [
            # Monthly recurring transactions
            {
                "name": "ACME Corp Direct Deposit",
                "merchant_name": "ACME Corporation",
                "amount": 3200.00,
                "description": "Bi-weekly salary payment",
                "category_match": "Salary & Wages",
                "frequency": "bi-weekly",
                "variance": 0.02
            },
            {
                "name": "Netflix Subscription",
                "merchant_name": "Netflix",
                "amount": -15.99,
                "description": "Monthly streaming service",
                "category_match": "Streaming Services",
                "frequency": "monthly",
                "variance": 0.0
            },
            {
                "name": "Spotify Premium",
                "merchant_name": "Spotify",
                "amount": -9.99,
                "description": "Music streaming subscription",
                "category_match": "Streaming Services",
                "frequency": "monthly",
                "variance": 0.0
            },
            {
                "name": "Pacific Electric Company",
                "merchant_name": "Pacific Electric",
                "amount": -125.00,
                "description": "Monthly electric bill",
                "category_match": "Utilities",
                "frequency": "monthly",
                "variance": 0.25
            },
            {
                "name": "Verizon Wireless",
                "merchant_name": "Verizon",
                "amount": -85.00,
                "description": "Monthly phone service",
                "category_match": "Phone",
                "frequency": "monthly",
                "variance": 0.05
            },
            {
                "name": "State Farm Insurance",
                "merchant_name": "State Farm",
                "amount": -150.00,
                "description": "Auto insurance premium",
                "category_match": "Insurance",
                "frequency": "monthly",
                "variance": 0.0
            },

            # Weekly recurring transactions
            {
                "name": "Whole Foods Market",
                "merchant_name": "Whole Foods",
                "amount": -85.00,
                "description": "Weekly grocery shopping",
                "category_match": "Groceries",
                "frequency": "weekly",
                "variance": 0.4
            },
            {
                "name": "Shell Gas Station",
                "merchant_name": "Shell",
                "amount": -45.00,
                "description": "Weekly fuel purchase",
                "category_match": "Gas & Fuel",
                "frequency": "weekly",
                "variance": 0.3
            },

            # Frequent random transactions
            {
                "name": "Starbucks Coffee",
                "merchant_name": "Starbucks",
                "amount": -5.75,
                "description": "Morning coffee",
                "category_match": "Coffee & Cafes",
                "frequency": "frequent",
                "variance": 0.5
            },
            {
                "name": "McDonald's",
                "merchant_name": "McDonald's",
                "amount": -8.50,
                "description": "Fast food lunch",
                "category_match": "Fast Food",
                "frequency": "frequent",
                "variance": 0.6
            },
            {
                "name": "Uber Trip",
                "merchant_name": "Uber",
                "amount": -15.00,
                "description": "Rideshare transportation",
                "category_match": "Rideshare & Taxi",
                "frequency": "frequent",
                "variance": 0.8
            },
            {
                "name": "CVS Pharmacy",
                "merchant_name": "CVS",
                "amount": -25.00,
                "description": "Pharmacy and convenience items",
                "category_match": "Pharmacy",
                "frequency": "occasional",
                "variance": 0.7
            },

            # Occasional larger purchases
            {
                "name": "Amazon Purchase",
                "merchant_name": "Amazon",
                "amount": -120.00,
                "description": "Online shopping",
                "category_match": "Online Shopping",
                "frequency": "occasional",
                "variance": 1.5
            },
            {
                "name": "Target Store",
                "merchant_name": "Target",
                "amount": -75.00,
                "description": "Household items and groceries",
                "category_match": "Department Stores",
                "frequency": "occasional",
                "variance": 0.8
            },
            {
                "name": "REI Co-op",
                "merchant_name": "REI",
                "amount": -200.00,
                "description": "Outdoor gear and clothing",
                "category_match": "Clothing & Accessories",
                "frequency": "rare",
                "variance": 1.0
            },
            {
                "name": "Dr. Smith Medical Group",
                "merchant_name": "Medical Associates",
                "amount": -150.00,
                "description": "Medical consultation",
                "category_match": "Medical & Dental",
                "frequency": "rare",
                "variance": 0.5
            },

            # Transfer and financial transactions
            {
                "name": "Transfer to Savings",
                "merchant_name": "First National Bank",
                "amount": -500.00,
                "description": "Monthly savings transfer",
                "category_match": "Bank Transfers",
                "frequency": "monthly",
                "variance": 0.1
            },
            {
                "name": "Venmo Payment",
                "merchant_name": "Venmo",
                "amount": -25.00,
                "description": "Split dinner bill",
                "category_match": "P2P Payments",
                "frequency": "occasional",
                "variance": 2.0
            },

            # Entertainment and leisure
            {
                "name": "AMC Theater",
                "merchant_name": "AMC",
                "amount": -28.00,
                "description": "Movie tickets",
                "category_match": "Movies & Events",
                "frequency": "occasional",
                "variance": 0.5
            },
            {
                "name": "Local Gym Membership",
                "merchant_name": "FitLife Gym",
                "amount": -45.00,
                "description": "Monthly gym membership",
                "category_match": None,  # Uncategorized for testing
                "frequency": "monthly",
                "variance": 0.0
            }
        ]

        # Generate transactions based on patterns
        transactions = []
        current_date = date.today() - timedelta(days=90)  # Start 3 months ago

        for pattern in transactions_data:
            # Generate multiple instances based on frequency
            frequency_map = {
                "bi-weekly": 6,  # 6 instances over 3 months
                "monthly": 3,    # 3 instances over 3 months
                "weekly": 12,    # 12 instances over 3 months
                "frequent": 25,  # 25 instances over 3 months
                "occasional": 8, # 8 instances over 3 months
                "rare": 2        # 2 instances over 3 months
            }

            instance_count = frequency_map.get(pattern["frequency"], 1)

            for i in range(instance_count):
                # Calculate transaction date based on frequency
                if pattern["frequency"] == "bi-weekly":
                    txn_date = current_date + timedelta(days=i * 14)
                elif pattern["frequency"] == "monthly":
                    txn_date = current_date + timedelta(days=i * 30)
                elif pattern["frequency"] == "weekly":
                    txn_date = current_date + timedelta(days=i * 7)
                else:
                    # Random distribution for frequent/occasional/rare
                    days_offset = int((90 / instance_count) * i + (i * 3))  # Spread evenly with some randomness
                    txn_date = current_date + timedelta(days=days_offset)

                # Apply amount variance
                base_amount = pattern["amount"]
                if pattern["variance"] > 0:
                    import random
                    variance_factor = 1 + (random.random() - 0.5) * pattern["variance"]
                    actual_amount = base_amount * variance_factor
                else:
                    actual_amount = base_amount

                # Find matching category for user_category
                user_category = None
                if pattern["category_match"]:
                    matching_category = next(
                        (cat for cat in categories if cat.name == pattern["category_match"]),
                        None
                    )
                    if matching_category:
                        user_category = matching_category.name

                transaction = Transaction(
                    account_id=account_id,
                    plaid_transaction_id=f"seed_txn_{len(transactions)}_{uuid4().hex[:8]}",
                    name=pattern["name"],
                    merchant_name=pattern["merchant_name"],
                    amount_cents=int(actual_amount * 100),
                    date=txn_date,
                    description=pattern["description"],
                    user_category=user_category,
                    pending=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(transaction)
                transactions.append(transaction)

        db.commit()
        logger.info(f"Created {len(transactions)} sample transactions")
        return transactions

    def create_ml_training_data(self, db: Session, transactions: List[Transaction]) -> int:
        """Set user categories on a subset of transactions for ML training."""
        logger.info("Creating ML training data...")

        # Set user categories on 70% of transactions for training
        training_count = int(len(transactions) * 0.7)

        labeled_count = 0
        for transaction in transactions[:training_count]:
            if not transaction.user_category:
                # Use a simple heuristic to assign categories for uncategorized transactions
                if transaction.amount > 0:
                    if transaction.amount > 1000:
                        transaction.user_category = "Salary & Wages"
                    else:
                        transaction.user_category = "Refunds & Reimbursements"
                else:
                    amount = abs(transaction.amount)
                    if amount < 20:
                        transaction.user_category = "Coffee & Cafes"
                    elif amount < 50:
                        transaction.user_category = "Fast Food"
                    elif amount < 100:
                        transaction.user_category = "Groceries"
                    else:
                        transaction.user_category = "Online Shopping"

                labeled_count += 1

        db.commit()
        logger.info(f"Added user categories to {labeled_count} additional transactions for ML training")
        return labeled_count

    def create_demo_user_and_account(self, db: Session) -> tuple:
        """Create a demo user and account for seeding."""
        logger.info("Creating demo user and account...")

        # Create demo user
        demo_user = User(
            email="demo@categorization.com",
            username="demo_categorization",
            hashed_password=hash_password("demo_password123"),
            full_name="Demo Categorization User",
            is_active=True,
            is_verified=True
        )
        db.add(demo_user)
        db.flush()

        # Create institution
        institution = Institution(
            plaid_institution_id="ins_demo_seed",
            name="Demo Bank for Seeding",
            logo_url="https://demo.com/logo.png",
            primary_color="#1976D2"
        )
        db.add(institution)
        db.flush()

        # Create Plaid item
        plaid_item = PlaidItem(
            user_id=demo_user.id,
            institution_id=institution.id,
            plaid_item_id="item_demo_seed",
            access_token="access-demo-seed-token",
            last_successful_sync=datetime.utcnow()
        )
        db.add(plaid_item)
        db.flush()

        # Create demo account
        demo_account = Account(
            user_id=demo_user.id,
            plaid_item_id=plaid_item.id,
            institution_id=institution.id,
            plaid_account_id="acc_demo_seed",
            name="Demo Primary Checking",
            official_name="Demo Bank Primary Checking Account",
            type="depository",
            subtype="checking",
            mask="0001",
            current_balance_cents=750000,  # $7,500.00
            available_balance_cents=725000,  # $7,250.00
            iso_currency_code="USD",
            is_active=True
        )
        db.add(demo_account)
        db.commit()

        logger.info(f"Created demo user: {demo_user.email}")
        logger.info(f"Created demo account: {demo_account.name}")

        return demo_user, demo_account

    def generate_seed_summary(self, categories: List[Category], transactions: List[Transaction]) -> Dict[str, Any]:
        """Generate a summary of seeded data."""
        category_counts = {}
        transaction_amounts = {"income": 0, "expenses": 0}

        for transaction in transactions:
            # Count by category
            category = transaction.user_category or "Uncategorized"
            category_counts[category] = category_counts.get(category, 0) + 1

            # Sum amounts
            if transaction.amount > 0:
                transaction_amounts["income"] += transaction.amount
            else:
                transaction_amounts["expenses"] += abs(transaction.amount)

        return {
            "categories": {
                "total": len(categories),
                "system_categories": len([c for c in categories if c.is_system]),
                "custom_categories": len([c for c in categories if not c.is_system]),
                "categories_with_rules": len([c for c in categories if c.rules])
            },
            "transactions": {
                "total": len(transactions),
                "with_categories": len([t for t in transactions if t.user_category]),
                "income_transactions": len([t for t in transactions if t.amount > 0]),
                "expense_transactions": len([t for t in transactions if t.amount < 0]),
                "total_income": transaction_amounts["income"],
                "total_expenses": transaction_amounts["expenses"],
                "net_amount": transaction_amounts["income"] - transaction_amounts["expenses"]
            },
            "category_distribution": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }

    def run_complete_seeding(self):
        """Run complete seeding process."""
        logger.info("Starting comprehensive categorization system seeding...")
        logger.info("=" * 60)

        db = self.SessionLocal()
        try:
            # Ensure tables exist
            Base.metadata.create_all(bind=self.engine)

            # Create demo user and account
            demo_user, demo_account = self.create_demo_user_and_account(db)

            # Create standard categories
            categories = self.create_standard_categories(db, str(demo_user.id))

            # Create sample transactions
            transactions = self.create_sample_transactions(db, str(demo_account.id), categories)

            # Create ML training data
            self.create_ml_training_data(db, transactions)

            # Generate summary
            summary = self.generate_seed_summary(categories, transactions)

            # Display results
            logger.info("\n" + "=" * 60)
            logger.info("SEEDING COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)

            logger.info(f"\nCategories Created:")
            logger.info(f"  Total categories: {summary['categories']['total']}")
            logger.info(f"  System categories: {summary['categories']['system_categories']}")
            logger.info(f"  Categories with rules: {summary['categories']['categories_with_rules']}")

            logger.info(f"\nTransactions Created:")
            logger.info(f"  Total transactions: {summary['transactions']['total']}")
            logger.info(f"  Categorized transactions: {summary['transactions']['with_categories']}")
            logger.info(f"  Income transactions: {summary['transactions']['income_transactions']}")
            logger.info(f"  Expense transactions: {summary['transactions']['expense_transactions']}")

            logger.info(f"\nFinancial Summary:")
            logger.info(f"  Total income: ${summary['transactions']['total_income']:,.2f}")
            logger.info(f"  Total expenses: ${summary['transactions']['total_expenses']:,.2f}")
            logger.info(f"  Net amount: ${summary['transactions']['net_amount']:,.2f}")

            logger.info(f"\nTop Categories by Transaction Count:")
            for category, count in list(summary['category_distribution'].items())[:5]:
                logger.info(f"  {category}: {count} transactions")

            logger.info(f"\nDemo Credentials:")
            logger.info(f"  Email: {demo_user.email}")
            logger.info(f"  Password: demo_password123")
            logger.info(f"  Account: {demo_account.name}")

            # Save summary to file
            with open("seed_summary.json", "w") as f:
                json.dump(summary, f, indent=2, default=str)

            logger.info(f"\nSeed summary saved to: seed_summary.json")

        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed Transaction Categorization Data")
    parser.add_argument(
        "--database-url",
        default="postgresql://manna:manna_password@localhost:5432/manna",
        help="Database URL for seeding"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Run seeding
    try:
        seeder = CategorySeeder(database_url=args.database_url)
        seeder.run_complete_seeding()
        logger.info("\nSeeding completed successfully!")
    except KeyboardInterrupt:
        logger.info("\nSeeding interrupted by user")
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        sys.exit(1)