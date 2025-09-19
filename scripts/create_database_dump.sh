#!/bin/bash

# Manna Financial Database Dump Script
# Creates a complete dump of the current database for replication

set -e

# Configuration
DB_NAME="manna"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DUMP_DIR="./backups/db_dumps"
SCHEMA_FILE="${DUMP_DIR}/manna_schema_${TIMESTAMP}.sql"
DATA_FILE="${DUMP_DIR}/manna_data_${TIMESTAMP}.sql"
FULL_DUMP_FILE="${DUMP_DIR}/manna_full_${TIMESTAMP}.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏦 Manna Financial Database Dump Script${NC}"
echo "=============================================="

# Create backup directory if it doesn't exist
mkdir -p "${DUMP_DIR}"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Database: ${DB_NAME}"
echo "  User: ${DB_USER}"
echo "  Host: ${DB_HOST}:${DB_PORT}"
echo "  Timestamp: ${TIMESTAMP}"
echo ""

# Test database connection
echo -e "${YELLOW}🔌 Testing database connection...${NC}"
if ! psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c '\q' 2>/dev/null; then
    echo -e "${RED}❌ Failed to connect to database. Please check your connection settings.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Database connection successful${NC}"

# 1. Create schema-only dump
echo -e "${YELLOW}📊 Creating schema dump...${NC}"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
    --schema-only \
    --no-owner \
    --no-privileges \
    --verbose \
    "${DB_NAME}" > "${SCHEMA_FILE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Schema dump created: ${SCHEMA_FILE}${NC}"
else
    echo -e "${RED}❌ Failed to create schema dump${NC}"
    exit 1
fi

# 2. Create data-only dump
echo -e "${YELLOW}💾 Creating data dump...${NC}"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
    --data-only \
    --no-owner \
    --no-privileges \
    --verbose \
    --column-inserts \
    "${DB_NAME}" > "${DATA_FILE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Data dump created: ${DATA_FILE}${NC}"
else
    echo -e "${RED}❌ Failed to create data dump${NC}"
    exit 1
fi

# 3. Create full dump (schema + data)
echo -e "${YELLOW}🗄️  Creating full dump...${NC}"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
    --no-owner \
    --no-privileges \
    --verbose \
    --column-inserts \
    "${DB_NAME}" > "${FULL_DUMP_FILE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Full dump created: ${FULL_DUMP_FILE}${NC}"
else
    echo -e "${RED}❌ Failed to create full dump${NC}"
    exit 1
fi

# 4. Generate restore script
RESTORE_SCRIPT="${DUMP_DIR}/restore_manna_${TIMESTAMP}.sh"
cat > "${RESTORE_SCRIPT}" << EOF
#!/bin/bash

# Manna Financial Database Restore Script
# Generated on: $(date)
#
# Usage: ./restore_manna_${TIMESTAMP}.sh [DATABASE_NAME] [DATABASE_USER] [DATABASE_HOST]
#
# Examples:
#   ./restore_manna_${TIMESTAMP}.sh                           # Uses defaults: manna, postgres, localhost
#   ./restore_manna_${TIMESTAMP}.sh manna_prod postgres prod-db.example.com
#   ./restore_manna_${TIMESTAMP}.sh manna_test testuser localhost

set -e

# Configuration with defaults
TARGET_DB_NAME="\${1:-manna}"
TARGET_DB_USER="\${2:-postgres}"
TARGET_DB_HOST="\${3:-localhost}"
TARGET_DB_PORT="\${4:-5432}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\${GREEN}🏦 Manna Financial Database Restore Script\${NC}"
echo "=============================================="
echo -e "\${YELLOW}📋 Target Configuration:\${NC}"
echo "  Database: \${TARGET_DB_NAME}"
echo "  User: \${TARGET_DB_USER}"
echo "  Host: \${TARGET_DB_HOST}:\${TARGET_DB_PORT}"
echo ""

# Test connection
echo -e "\${YELLOW}🔌 Testing database connection...\${NC}"
if ! psql -h "\${TARGET_DB_HOST}" -p "\${TARGET_DB_PORT}" -U "\${TARGET_DB_USER}" -d postgres -c '\q' 2>/dev/null; then
    echo -e "\${RED}❌ Failed to connect to database server. Please check your connection settings.\${NC}"
    exit 1
fi

# Check if database exists
echo -e "\${YELLOW}🔍 Checking if database '\${TARGET_DB_NAME}' exists...\${NC}"
DB_EXISTS=\$(psql -h "\${TARGET_DB_HOST}" -p "\${TARGET_DB_PORT}" -U "\${TARGET_DB_USER}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='\${TARGET_DB_NAME}'")

if [ "\${DB_EXISTS}" = "1" ]; then
    echo -e "\${YELLOW}⚠️  Database '\${TARGET_DB_NAME}' already exists.\${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ \$REPLY =~ ^[Yy]$ ]]; then
        echo -e "\${YELLOW}🗑️  Dropping existing database...\${NC}"
        psql -h "\${TARGET_DB_HOST}" -p "\${TARGET_DB_PORT}" -U "\${TARGET_DB_USER}" -d postgres -c "DROP DATABASE \${TARGET_DB_NAME};"
    else
        echo -e "\${RED}❌ Restore cancelled.\${NC}"
        exit 1
    fi
fi

# Create database
echo -e "\${YELLOW}🏗️  Creating database '\${TARGET_DB_NAME}'...\${NC}"
psql -h "\${TARGET_DB_HOST}" -p "\${TARGET_DB_PORT}" -U "\${TARGET_DB_USER}" -d postgres -c "CREATE DATABASE \${TARGET_DB_NAME};"

# Restore from full dump
echo -e "\${YELLOW}📥 Restoring database from dump...\${NC}"
psql -h "\${TARGET_DB_HOST}" -p "\${TARGET_DB_PORT}" -U "\${TARGET_DB_USER}" -d "\${TARGET_DB_NAME}" -f "manna_full_${TIMESTAMP}.sql"

if [ \$? -eq 0 ]; then
    echo -e "\${GREEN}✅ Database restore completed successfully!\${NC}"
    echo ""
    echo -e "\${YELLOW}📊 Database Summary:\${NC}"
    psql -h "\${TARGET_DB_HOST}" -p "\${TARGET_DB_PORT}" -U "\${TARGET_DB_USER}" -d "\${TARGET_DB_NAME}" -c "
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
    echo -e "\${RED}❌ Database restore failed!\${NC}"
    exit 1
fi
EOF

chmod +x "${RESTORE_SCRIPT}"

# 5. Generate summary
echo ""
echo -e "${GREEN}📋 DUMP SUMMARY${NC}"
echo "=============================================="
echo "Schema dump:    $(basename "${SCHEMA_FILE}")"
echo "Data dump:      $(basename "${DATA_FILE}")"
echo "Full dump:      $(basename "${FULL_DUMP_FILE}")"
echo "Restore script: $(basename "${RESTORE_SCRIPT}")"
echo ""
echo "File sizes:"
ls -lh "${SCHEMA_FILE}" "${DATA_FILE}" "${FULL_DUMP_FILE}" | awk '{print "  " $9 ": " $5}'
echo ""

# 6. Show database statistics
echo -e "${YELLOW}📊 Current Database Statistics:${NC}"
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "
SELECT
    schemaname as schema,
    tablename as table,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY schemaname, tablename;
"

echo ""
echo -e "${GREEN}✅ Database dump completed successfully!${NC}"
echo -e "${YELLOW}📁 All files saved to: ${DUMP_DIR}${NC}"
echo ""
echo -e "${YELLOW}🚀 To restore on another system:${NC}"
echo "1. Copy the dump directory to the target system"
echo "2. Run: ./$(basename "${RESTORE_SCRIPT}") [db_name] [user] [host]"
echo ""