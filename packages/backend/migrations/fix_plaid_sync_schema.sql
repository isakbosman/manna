-- Migration to fix Plaid sync schema issues
-- Run this to ensure your database is properly configured

-- 1. Verify plaid_items table has correct cursor column
DO $$
BEGIN
    -- Check if sync_cursor exists and rename to cursor
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name = 'sync_cursor'
    ) THEN
        ALTER TABLE plaid_items RENAME COLUMN sync_cursor TO cursor;
        RAISE NOTICE 'Renamed sync_cursor to cursor';
    END IF;

    -- Ensure cursor column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name = 'cursor'
    ) THEN
        ALTER TABLE plaid_items ADD COLUMN cursor VARCHAR(255);
        RAISE NOTICE 'Added cursor column';
    END IF;

    -- Add indexes for performance
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'plaid_items'
        AND indexname = 'idx_plaid_items_cursor'
    ) THEN
        CREATE INDEX idx_plaid_items_cursor ON plaid_items(cursor);
        RAISE NOTICE 'Added index on cursor column';
    END IF;
END $$;

-- 2. Verify transactions table has correct structure
DO $$
BEGIN
    -- Check for amount_cents column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions'
        AND column_name = 'amount_cents'
    ) THEN
        -- If we have amount as numeric, convert to cents
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'transactions'
            AND column_name = 'amount'
            AND data_type = 'numeric'
        ) THEN
            ALTER TABLE transactions ADD COLUMN amount_cents INTEGER;
            UPDATE transactions SET amount_cents = CAST(amount * 100 AS INTEGER);
            RAISE NOTICE 'Added amount_cents column and migrated data';
        ELSE
            ALTER TABLE transactions ADD COLUMN amount_cents INTEGER;
            RAISE NOTICE 'Added amount_cents column';
        END IF;
    END IF;

    -- Ensure transaction_type exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions'
        AND column_name = 'transaction_type'
    ) THEN
        ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(10);
        -- Default all existing to debit (can be updated later)
        UPDATE transactions SET transaction_type =
            CASE
                WHEN amount_cents > 0 THEN 'debit'
                ELSE 'credit'
            END
        WHERE transaction_type IS NULL;
        RAISE NOTICE 'Added transaction_type column';
    END IF;

    -- Ensure proper indexes on transactions
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'transactions'
        AND indexname = 'idx_transactions_plaid_id'
    ) THEN
        CREATE UNIQUE INDEX idx_transactions_plaid_id ON transactions(plaid_transaction_id);
        RAISE NOTICE 'Added unique index on plaid_transaction_id';
    END IF;
END $$;

-- 3. Clean up any invalid cursor values
UPDATE plaid_items
SET cursor = NULL
WHERE cursor = '';

-- 4. Add status column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name = 'status'
    ) THEN
        ALTER TABLE plaid_items ADD COLUMN status VARCHAR(20) DEFAULT 'active';
        RAISE NOTICE 'Added status column';
    END IF;
END $$;

-- 5. Add error tracking columns if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name = 'error_code'
    ) THEN
        ALTER TABLE plaid_items ADD COLUMN error_code VARCHAR(50);
        RAISE NOTICE 'Added error_code column';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name = 'error_message'
    ) THEN
        ALTER TABLE plaid_items ADD COLUMN error_message TEXT;
        RAISE NOTICE 'Added error_message column';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name = 'requires_reauth'
    ) THEN
        ALTER TABLE plaid_items ADD COLUMN requires_reauth BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added requires_reauth column';
    END IF;
END $$;

-- 6. Summary of current state
SELECT
    'plaid_items' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN cursor IS NOT NULL AND cursor != '' THEN 1 END) as items_with_cursor,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_items,
    COUNT(CASE WHEN requires_reauth = true THEN 1 END) as needs_reauth
FROM plaid_items

UNION ALL

SELECT
    'transactions' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT plaid_transaction_id) as unique_transactions,
    COUNT(CASE WHEN transaction_type = 'debit' THEN 1 END) as debits,
    COUNT(CASE WHEN transaction_type = 'credit' THEN 1 END) as credits
FROM transactions;

-- Display success message
SELECT '✅ Schema migration completed successfully!' as status;