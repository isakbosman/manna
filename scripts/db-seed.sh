#!/bin/bash

# Database Seeding Script for Manna Development Environment
# This script seeds the database with sample data for testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SEED]${NC} $1"
}

echo "🌱 Seeding Manna Database with Sample Data..."

# Check if Docker Compose services are running
if ! docker-compose ps postgres | grep -q "Up"; then
    print_error "PostgreSQL service is not running. Please start it first with: docker-compose up -d postgres"
    exit 1
fi

# Create temporary SQL file for seeding
SEED_FILE="/tmp/seed_data.sql"

print_header "Creating seed data..."

cat > "$SEED_FILE" << 'EOF'
-- Sample data for Manna development

-- Insert sample accounts
INSERT INTO accounts (account_id, account_name, account_type, account_subtype, institution_name, institution_id) VALUES
    ('acc_sample_checking', 'Sample Checking Account', 'depository', 'checking', 'Sample Bank', 'ins_sample'),
    ('acc_sample_savings', 'Sample Savings Account', 'depository', 'savings', 'Sample Bank', 'ins_sample'),
    ('acc_sample_credit', 'Sample Credit Card', 'credit', 'credit card', 'Sample Credit Union', 'ins_sample_credit')
ON CONFLICT (account_id) DO NOTHING;

-- Insert sample categorization rules
INSERT INTO categorization_rules (rule_name, match_type, match_value, category, subcategory, priority) VALUES
    ('Grocery Stores', 'contains', 'GROCERY', 'Food & Dining', 'Groceries', 10),
    ('Gas Stations', 'contains', 'GAS', 'Transportation', 'Gas', 10),
    ('Restaurants', 'contains', 'RESTAURANT', 'Food & Dining', 'Restaurants', 8),
    ('Coffee Shops', 'contains', 'COFFEE', 'Food & Dining', 'Coffee', 9),
    ('Streaming Services', 'contains', 'NETFLIX', 'Entertainment', 'Streaming', 10),
    ('Streaming Services', 'contains', 'SPOTIFY', 'Entertainment', 'Streaming', 10),
    ('Uber/Lyft', 'contains', 'UBER', 'Transportation', 'Rideshare', 10),
    ('Uber/Lyft', 'contains', 'LYFT', 'Transportation', 'Rideshare', 10),
    ('Amazon', 'contains', 'AMAZON', 'Shopping', 'Online', 7),
    ('Pharmacy', 'contains', 'PHARMACY', 'Healthcare', 'Pharmacy', 10),
    ('ATM Withdrawal', 'contains', 'ATM', 'Transfer', 'Cash Withdrawal', 10)
ON CONFLICT (rule_name, match_value) DO NOTHING;

-- Insert sample transactions (last 30 days)
INSERT INTO transactions (transaction_id, account_id, amount, date, description, merchant_name, category, subcategory) VALUES
    ('txn_001', 'acc_sample_checking', -45.67, CURRENT_DATE - INTERVAL '1 day', 'WHOLE FOODS MARKET', 'Whole Foods', 'Food & Dining', 'Groceries'),
    ('txn_002', 'acc_sample_checking', -3200.00, CURRENT_DATE - INTERVAL '2 days', 'RENT PAYMENT', 'Landlord', 'Bills & Utilities', 'Rent'),
    ('txn_003', 'acc_sample_checking', 5000.00, CURRENT_DATE - INTERVAL '3 days', 'SALARY DEPOSIT', 'Company Inc', 'Income', 'Salary'),
    ('txn_004', 'acc_sample_credit', -89.99, CURRENT_DATE - INTERVAL '4 days', 'AMAZON.COM', 'Amazon', 'Shopping', 'Online'),
    ('txn_005', 'acc_sample_checking', -12.50, CURRENT_DATE - INTERVAL '5 days', 'STARBUCKS COFFEE', 'Starbucks', 'Food & Dining', 'Coffee'),
    ('txn_006', 'acc_sample_checking', -65.43, CURRENT_DATE - INTERVAL '6 days', 'SHELL GAS STATION', 'Shell', 'Transportation', 'Gas'),
    ('txn_007', 'acc_sample_credit', -15.99, CURRENT_DATE - INTERVAL '7 days', 'NETFLIX.COM', 'Netflix', 'Entertainment', 'Streaming'),
    ('txn_008', 'acc_sample_checking', -25.00, CURRENT_DATE - INTERVAL '8 days', 'UBER TRIP', 'Uber', 'Transportation', 'Rideshare'),
    ('txn_009', 'acc_sample_savings', 500.00, CURRENT_DATE - INTERVAL '9 days', 'TRANSFER FROM CHECKING', 'Internal', 'Transfer', 'Savings'),
    ('txn_010', 'acc_sample_checking', -500.00, CURRENT_DATE - INTERVAL '9 days', 'TRANSFER TO SAVINGS', 'Internal', 'Transfer', 'Savings'),
    ('txn_011', 'acc_sample_checking', -125.00, CURRENT_DATE - INTERVAL '10 days', 'ELECTRIC BILL', 'Power Company', 'Bills & Utilities', 'Electricity'),
    ('txn_012', 'acc_sample_credit', -67.89, CURRENT_DATE - INTERVAL '12 days', 'TARGET STORE', 'Target', 'Shopping', 'Retail'),
    ('txn_013', 'acc_sample_checking', -35.00, CURRENT_DATE - INTERVAL '14 days', 'RESTAURANT DINING', 'Local Bistro', 'Food & Dining', 'Restaurants'),
    ('txn_014', 'acc_sample_checking', -19.99, CURRENT_DATE - INTERVAL '15 days', 'SPOTIFY PREMIUM', 'Spotify', 'Entertainment', 'Streaming'),
    ('txn_015', 'acc_sample_checking', -200.00, CURRENT_DATE - INTERVAL '18 days', 'ATM WITHDRAWAL', 'Bank ATM', 'Transfer', 'Cash Withdrawal'),
    ('txn_016', 'acc_sample_credit', -45.00, CURRENT_DATE - INTERVAL '20 days', 'CVS PHARMACY', 'CVS', 'Healthcare', 'Pharmacy'),
    ('txn_017', 'acc_sample_checking', -78.90, CURRENT_DATE - INTERVAL '22 days', 'INTERNET BILL', 'ISP Company', 'Bills & Utilities', 'Internet'),
    ('txn_018', 'acc_sample_checking', -156.78, CURRENT_DATE - INTERVAL '25 days', 'GROCERY SHOPPING', 'Safeway', 'Food & Dining', 'Groceries'),
    ('txn_019', 'acc_sample_checking', 2500.00, CURRENT_DATE - INTERVAL '28 days', 'FREELANCE PAYMENT', 'Client ABC', 'Income', 'Freelance'),
    ('txn_020', 'acc_sample_credit', -299.99, CURRENT_DATE - INTERVAL '30 days', 'LAPTOP PURCHASE', 'Best Buy', 'Shopping', 'Electronics')
ON CONFLICT (transaction_id) DO NOTHING;

-- Update transaction counts
SELECT COUNT(*) as total_transactions FROM transactions;
SELECT COUNT(*) as total_accounts FROM accounts;
SELECT COUNT(*) as total_rules FROM categorization_rules;
EOF

print_status "Executing seed data SQL..."

# Execute the seed file
docker-compose exec -T postgres psql -U manna_user -d manna_db -f - < "$SEED_FILE"

if [ $? -eq 0 ]; then
    print_status "Database seeded successfully!"
else
    print_error "Failed to seed database"
    rm -f "$SEED_FILE"
    exit 1
fi

# Clean up temp file
rm -f "$SEED_FILE"

print_header "Seed data summary:"
echo "  • 3 sample accounts (checking, savings, credit card)"
echo "  • 20 sample transactions from the last 30 days"
echo "  • 11 categorization rules for common merchants"
echo "  • Sample income, expenses, and transfers"
echo ""
print_status "Database seeding complete! 🌱"
echo "You can now test the application with realistic sample data."
echo "Visit http://localhost:8501 to see the dashboard with sample data."
