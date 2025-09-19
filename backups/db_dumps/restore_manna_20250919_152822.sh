#!/bin/bash

# Manna Financial Database Restore Script
# Generated on: Fri Sep 19 15:28:22 PDT 2025
#
# Usage: ./restore_manna_20250919_152822.sh [DATABASE_NAME] [DATABASE_USER] [DATABASE_HOST]
#
# Examples:
#   ./restore_manna_20250919_152822.sh                           # Uses defaults: manna, postgres, localhost
#   ./restore_manna_20250919_152822.sh manna_prod postgres prod-db.example.com
#   ./restore_manna_20250919_152822.sh manna_test testuser localhost

set -e

# Configuration with defaults
TARGET_DB_NAME="${1:-manna}"
TARGET_DB_USER="${2:-postgres}"
TARGET_DB_HOST="${3:-localhost}"
TARGET_DB_PORT="${4:-5432}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🏦 Manna Financial Database Restore Script${NC}"
echo "=============================================="
echo -e "${YELLOW}📋 Target Configuration:${NC}"
echo "  Database: ${TARGET_DB_NAME}"
echo "  User: ${TARGET_DB_USER}"
echo "  Host: ${TARGET_DB_HOST}:${TARGET_DB_PORT}"
echo ""

# Test connection
echo -e "${YELLOW}🔌 Testing database connection...${NC}"
if ! psql -h "${TARGET_DB_HOST}" -p "${TARGET_DB_PORT}" -U "${TARGET_DB_USER}" -d postgres -c '\q' 2>/dev/null; then
    echo -e "${RED}❌ Failed to connect to database server. Please check your connection settings.${NC}"
    exit 1
fi

# Check if database exists
echo -e "${YELLOW}🔍 Checking if database '${TARGET_DB_NAME}' exists...${NC}"
DB_EXISTS=$(psql -h "${TARGET_DB_HOST}" -p "${TARGET_DB_PORT}" -U "${TARGET_DB_USER}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${TARGET_DB_NAME}'")

if [ "${DB_EXISTS}" = "1" ]; then
    echo -e "${YELLOW}⚠️  Database '${TARGET_DB_NAME}' already exists.${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🗑️  Dropping existing database...${NC}"
        psql -h "${TARGET_DB_HOST}" -p "${TARGET_DB_PORT}" -U "${TARGET_DB_USER}" -d postgres -c "DROP DATABASE ${TARGET_DB_NAME};"
    else
        echo -e "${RED}❌ Restore cancelled.${NC}"
        exit 1
    fi
fi

# Create database
echo -e "${YELLOW}🏗️  Creating database '${TARGET_DB_NAME}'...${NC}"
psql -h "${TARGET_DB_HOST}" -p "${TARGET_DB_PORT}" -U "${TARGET_DB_USER}" -d postgres -c "CREATE DATABASE ${TARGET_DB_NAME};"

# Restore from full dump
echo -e "${YELLOW}📥 Restoring database from dump...${NC}"
psql -h "${TARGET_DB_HOST}" -p "${TARGET_DB_PORT}" -U "${TARGET_DB_USER}" -d "${TARGET_DB_NAME}" -f "manna_full_20250919_152822.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database restore completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}📊 Database Summary:${NC}"
    psql -h "${TARGET_DB_HOST}" -p "${TARGET_DB_PORT}" -U "${TARGET_DB_USER}" -d "${TARGET_DB_NAME}" -c "
        SELECT
            schemaname as schema,
            tablename as table,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes
        FROM pg_stat_user_tables
        ORDER BY schemaname, tablename;
    "
else
    echo -e "${RED}❌ Database restore failed!${NC}"
    exit 1
fi
