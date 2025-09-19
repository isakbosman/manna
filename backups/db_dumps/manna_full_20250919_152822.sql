--
-- PostgreSQL database dump
--

-- Dumped from database version 17.0 (Postgres.app)
-- Dumped by pg_dump version 17.0 (Postgres.app)

-- Started on 2025-09-19 15:28:22 PDT

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 237 (class 1259 OID 43155)
-- Name: accounting_periods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounting_periods (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    period_name character varying(100) NOT NULL,
    period_type character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    is_closed boolean,
    closing_date timestamp with time zone,
    closing_journal_entry_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- TOC entry 222 (class 1259 OID 42653)
-- Name: accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounts (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    institution_id uuid,
    plaid_item_id uuid,
    plaid_account_id character varying(255),
    plaid_persistent_id character varying(255),
    name character varying(255) NOT NULL,
    official_name character varying(255),
    account_type character varying(50) NOT NULL,
    account_subtype character varying(50),
    is_business boolean NOT NULL,
    is_active boolean NOT NULL,
    is_manual boolean NOT NULL,
    current_balance numeric(15,2),
    available_balance numeric(15,2),
    credit_limit numeric(15,2),
    minimum_balance numeric(15,2),
    account_number_masked character varying(20),
    routing_number character varying(20),
    last_sync timestamp with time zone,
    sync_status character varying(20),
    error_code character varying(50),
    error_message text,
    metadata jsonb,
    iso_currency_code character varying(3) DEFAULT 'USD'::character varying,
    CONSTRAINT ck_account_type CHECK (((account_type)::text = ANY ((ARRAY['depository'::character varying, 'credit'::character varying, 'loan'::character varying, 'investment'::character varying, 'other'::character varying, 'checking'::character varying, 'savings'::character varying])::text[]))),
    CONSTRAINT ck_sync_status CHECK (((sync_status)::text = ANY ((ARRAY['active'::character varying, 'error'::character varying, 'disconnected'::character varying, 'pending'::character varying])::text[])))
);


--
-- TOC entry 217 (class 1259 OID 42579)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- TOC entry 231 (class 1259 OID 42931)
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid,
    session_id uuid,
    action character varying(100) NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id character varying(100),
    old_values jsonb,
    new_values jsonb,
    changes_summary text,
    event_timestamp timestamp with time zone NOT NULL,
    source character varying(50),
    user_agent character varying(500),
    ip_address inet,
    request_id character varying(100),
    endpoint character varying(200),
    http_method character varying(10),
    status_code integer,
    business_impact character varying(20),
    compliance_relevant boolean,
    financial_impact boolean,
    metadata jsonb,
    tags jsonb,
    error_code character varying(50),
    error_message text
);


--
-- TOC entry 238 (class 1259 OID 43170)
-- Name: bookkeeping_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bookkeeping_rules (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    rule_name character varying(255) NOT NULL,
    rule_type character varying(50) NOT NULL,
    trigger_conditions jsonb NOT NULL,
    journal_template jsonb,
    is_active boolean,
    priority integer,
    last_executed timestamp with time zone,
    execution_count integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- TOC entry 229 (class 1259 OID 42872)
-- Name: budget_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_items (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    budget_id uuid NOT NULL,
    category_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    budgeted_amount numeric(15,2) NOT NULL,
    actual_amount numeric(15,2),
    item_type character varying(20),
    is_fixed boolean,
    is_essential boolean,
    alert_threshold numeric(3,2),
    last_updated timestamp with time zone,
    allow_rollover boolean,
    rollover_amount numeric(15,2),
    notes text,
    metadata jsonb,
    CONSTRAINT ck_budget_item_type CHECK (((item_type)::text = ANY ((ARRAY['income'::character varying, 'expense'::character varying, 'savings'::character varying, 'transfer'::character varying])::text[]))),
    CONSTRAINT ck_budgeted_amount_positive CHECK ((budgeted_amount >= (0)::numeric)),
    CONSTRAINT ck_item_alert_threshold_range CHECK (((alert_threshold IS NULL) OR ((alert_threshold > (0)::numeric) AND (alert_threshold <= (1)::numeric))))
);


--
-- TOC entry 228 (class 1259 OID 42847)
-- Name: budgets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budgets (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    budget_type character varying(20),
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    is_business_budget boolean NOT NULL,
    is_active boolean NOT NULL,
    is_template boolean,
    total_income_target numeric(15,2),
    total_expense_target numeric(15,2),
    savings_target numeric(15,2),
    status character varying(20),
    last_reviewed timestamp with time zone,
    alert_threshold numeric(3,2),
    enable_alerts boolean,
    tags jsonb,
    metadata jsonb,
    CONSTRAINT ck_alert_threshold_range CHECK (((alert_threshold > (0)::numeric) AND (alert_threshold <= (1)::numeric))),
    CONSTRAINT ck_budget_status CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'active'::character varying, 'completed'::character varying, 'archived'::character varying])::text[]))),
    CONSTRAINT ck_budget_type CHECK (((budget_type)::text = ANY ((ARRAY['monthly'::character varying, 'quarterly'::character varying, 'annual'::character varying, 'custom'::character varying])::text[]))),
    CONSTRAINT ck_valid_budget_period CHECK ((period_end > period_start))
);


--
-- TOC entry 234 (class 1259 OID 43009)
-- Name: business_expense_tracking; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_expense_tracking (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    transaction_id uuid NOT NULL,
    user_id uuid NOT NULL,
    business_purpose text,
    business_percentage numeric(5,2),
    receipt_required boolean,
    receipt_attached boolean,
    receipt_url character varying(500),
    mileage_start_location character varying(255),
    mileage_end_location character varying(255),
    miles_driven numeric(8,2),
    vehicle_info jsonb,
    depreciation_method character varying(50),
    depreciation_years integer,
    section_179_eligible boolean,
    substantiation_notes text,
    audit_trail jsonb,
    CONSTRAINT ck_business_percentage CHECK (((business_percentage >= (0)::numeric) AND (business_percentage <= (100)::numeric))),
    CONSTRAINT ck_depreciation_years_positive CHECK ((depreciation_years > 0)),
    CONSTRAINT ck_miles_positive CHECK ((miles_driven >= (0)::numeric))
);


--
-- TOC entry 220 (class 1259 OID 42609)
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid,
    name character varying(100) NOT NULL,
    parent_category character varying(100),
    description text,
    color character varying(7),
    icon character varying(50),
    is_system boolean NOT NULL,
    is_active boolean NOT NULL,
    rules jsonb
);


--
-- TOC entry 236 (class 1259 OID 43073)
-- Name: categorization_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categorization_audit (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    transaction_id uuid NOT NULL,
    user_id uuid NOT NULL,
    action_type character varying(50) NOT NULL,
    old_category_id uuid,
    new_category_id uuid,
    old_tax_category_id uuid,
    new_tax_category_id uuid,
    old_chart_account_id uuid,
    new_chart_account_id uuid,
    reason character varying(255),
    confidence_before numeric(5,4),
    confidence_after numeric(5,4),
    automated boolean,
    ml_model_version character varying(50),
    processing_time_ms integer,
    audit_metadata jsonb,
    CONSTRAINT ck_action_type CHECK (((action_type)::text = ANY ((ARRAY['categorize'::character varying, 'recategorize'::character varying, 'tax_categorize'::character varying, 'chart_assign'::character varying, 'bulk_update'::character varying])::text[])))
);


--
-- TOC entry 226 (class 1259 OID 42782)
-- Name: categorization_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categorization_rules (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    category_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    rule_type character varying(50) NOT NULL,
    pattern character varying(1000) NOT NULL,
    pattern_type character varying(20),
    case_sensitive boolean,
    match_fields jsonb,
    conditions jsonb,
    priority integer NOT NULL,
    is_active boolean NOT NULL,
    is_system_rule boolean,
    auto_apply boolean,
    requires_approval boolean,
    set_business boolean,
    set_tax_deductible boolean,
    match_count integer,
    last_matched timestamp with time zone,
    accuracy_score integer,
    tags jsonb,
    metadata jsonb,
    CONSTRAINT ck_accuracy_range CHECK (((accuracy_score >= '-100'::integer) AND (accuracy_score <= 100))),
    CONSTRAINT ck_pattern_type CHECK (((pattern_type)::text = ANY ((ARRAY['contains'::character varying, 'exact'::character varying, 'regex'::character varying, 'starts_with'::character varying, 'ends_with'::character varying, 'fuzzy'::character varying])::text[]))),
    CONSTRAINT ck_priority_range CHECK (((priority >= 0) AND (priority <= 1000))),
    CONSTRAINT ck_rule_type CHECK (((rule_type)::text = ANY ((ARRAY['merchant'::character varying, 'keyword'::character varying, 'amount'::character varying, 'regex'::character varying, 'compound'::character varying, 'ml_assisted'::character varying])::text[])))
);


--
-- TOC entry 235 (class 1259 OID 43036)
-- Name: category_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.category_mappings (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    source_category_id uuid NOT NULL,
    chart_account_id uuid NOT NULL,
    tax_category_id uuid NOT NULL,
    confidence_score numeric(5,4),
    is_user_defined boolean,
    is_active boolean,
    effective_date date NOT NULL,
    expiration_date date,
    business_percentage_default numeric(5,2),
    always_require_receipt boolean,
    auto_substantiation_rules jsonb,
    mapping_notes text,
    CONSTRAINT ck_confidence_score CHECK (((confidence_score >= (0)::numeric) AND (confidence_score <= (1)::numeric))),
    CONSTRAINT ck_default_business_percentage CHECK (((business_percentage_default >= (0)::numeric) AND (business_percentage_default <= (100)::numeric)))
);


--
-- TOC entry 232 (class 1259 OID 42965)
-- Name: chart_of_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chart_of_accounts (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    account_code character varying(20) NOT NULL,
    account_name character varying(255) NOT NULL,
    account_type character varying(50) NOT NULL,
    parent_account_id uuid,
    description text,
    normal_balance character varying(10) NOT NULL,
    is_active boolean NOT NULL,
    is_system_account boolean NOT NULL,
    current_balance numeric(15,2),
    tax_category character varying(100),
    tax_line_mapping character varying(100),
    requires_1099 boolean,
    account_metadata jsonb,
    CONSTRAINT ck_account_type CHECK (((account_type)::text = ANY ((ARRAY['asset'::character varying, 'liability'::character varying, 'equity'::character varying, 'revenue'::character varying, 'expense'::character varying, 'contra_asset'::character varying, 'contra_liability'::character varying, 'contra_equity'::character varying])::text[]))),
    CONSTRAINT ck_normal_balance CHECK (((normal_balance)::text = ANY ((ARRAY['debit'::character varying, 'credit'::character varying])::text[])))
);


--
-- TOC entry 219 (class 1259 OID 42597)
-- Name: institutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.institutions (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    plaid_institution_id character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    country_codes jsonb DEFAULT '[]'::jsonb,
    products jsonb DEFAULT '[]'::jsonb,
    routing_numbers jsonb DEFAULT '[]'::jsonb,
    logo character varying(500),
    primary_color character varying(7),
    url character varying(500),
    is_active boolean DEFAULT true NOT NULL,
    oauth_required boolean DEFAULT false,
    metadata jsonb DEFAULT '{}'::jsonb
);


--
-- TOC entry 239 (class 1259 OID 43186)
-- Name: journal_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.journal_entries (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    entry_number character varying(50) NOT NULL,
    entry_date date NOT NULL,
    description text NOT NULL,
    reference character varying(100),
    journal_type character varying(20),
    total_debits numeric(15,2) NOT NULL,
    total_credits numeric(15,2) NOT NULL,
    is_balanced boolean,
    is_posted boolean,
    posting_date timestamp with time zone,
    period_id uuid,
    source_type character varying(50),
    automation_rule_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- TOC entry 240 (class 1259 OID 43216)
-- Name: journal_entry_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.journal_entry_lines (
    id uuid NOT NULL,
    journal_entry_id uuid NOT NULL,
    chart_account_id uuid,
    debit_amount numeric(15,2),
    credit_amount numeric(15,2),
    description text,
    transaction_id uuid,
    line_number integer NOT NULL,
    tax_category_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- TOC entry 225 (class 1259 OID 42754)
-- Name: ml_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ml_predictions (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    transaction_id uuid NOT NULL,
    category_id uuid NOT NULL,
    model_version character varying(50) NOT NULL,
    model_type character varying(50) NOT NULL,
    confidence numeric(5,4) NOT NULL,
    probability numeric(5,4) NOT NULL,
    alternative_predictions jsonb,
    features_used jsonb,
    feature_importance jsonb,
    prediction_date timestamp with time zone NOT NULL,
    processing_time_ms integer,
    is_accepted boolean,
    user_feedback character varying(20),
    feedback_date timestamp with time zone,
    is_outlier boolean,
    requires_review boolean,
    review_reason character varying(100),
    CONSTRAINT ck_confidence_range CHECK (((confidence >= 0.0) AND (confidence <= 1.0))),
    CONSTRAINT ck_probability_range CHECK (((probability >= 0.0) AND (probability <= 1.0))),
    CONSTRAINT ck_user_feedback CHECK (((user_feedback)::text = ANY ((ARRAY['correct'::character varying, 'incorrect'::character varying, 'partial'::character varying, 'unsure'::character varying])::text[])))
);


--
-- TOC entry 221 (class 1259 OID 42626)
-- Name: plaid_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plaid_items (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    institution_id uuid NOT NULL,
    plaid_item_id character varying(255) NOT NULL,
    access_token character varying(255) NOT NULL,
    status character varying(20) NOT NULL,
    error_code character varying(50),
    error_message text,
    available_products jsonb,
    billed_products jsonb,
    webhook_url character varying(500),
    consent_expiration_time timestamp with time zone,
    last_successful_sync timestamp with time zone,
    last_sync_attempt timestamp with time zone,
    cursor character varying(255),
    max_days_back integer,
    sync_frequency_hours integer,
    is_active boolean NOT NULL,
    requires_reauth boolean,
    has_mfa boolean,
    update_type character varying(20),
    metadata jsonb,
    version integer DEFAULT 1 NOT NULL,
    CONSTRAINT ck_max_days_back CHECK (((max_days_back > 0) AND (max_days_back <= 730))),
    CONSTRAINT ck_plaid_item_status CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'error'::character varying, 'expired'::character varying, 'revoked'::character varying, 'pending'::character varying])::text[]))),
    CONSTRAINT ck_sync_frequency CHECK (((sync_frequency_hours >= 1) AND (sync_frequency_hours <= 168)))
);


--
-- TOC entry 230 (class 1259 OID 42900)
-- Name: plaid_webhooks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plaid_webhooks (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    plaid_item_id uuid,
    webhook_type character varying(50) NOT NULL,
    webhook_code character varying(50) NOT NULL,
    plaid_item_id_raw character varying(255),
    plaid_environment character varying(20),
    event_data jsonb NOT NULL,
    new_transactions integer,
    modified_transactions integer,
    removed_transactions integer,
    processing_status character varying(20),
    processed_at timestamp with time zone,
    processing_duration_ms integer,
    error_code character varying(50),
    error_message text,
    retry_count integer,
    max_retries integer,
    received_at timestamp with time zone NOT NULL,
    user_agent character varying(500),
    source_ip character varying(45),
    webhook_hash character varying(64),
    is_duplicate boolean,
    original_webhook_id uuid,
    CONSTRAINT ck_plaid_environment CHECK (((plaid_environment)::text = ANY ((ARRAY['sandbox'::character varying, 'development'::character varying, 'production'::character varying])::text[]))),
    CONSTRAINT ck_processing_status CHECK (((processing_status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying, 'ignored'::character varying])::text[]))),
    CONSTRAINT ck_retry_count CHECK (((retry_count >= 0) AND (retry_count <= max_retries))),
    CONSTRAINT ck_webhook_type CHECK (((webhook_type)::text = ANY ((ARRAY['TRANSACTIONS'::character varying, 'AUTH'::character varying, 'IDENTITY'::character varying, 'ASSETS'::character varying, 'HOLDINGS'::character varying, 'ITEM'::character varying, 'INCOME'::character varying, 'LIABILITIES'::character varying])::text[])))
);


--
-- TOC entry 242 (class 1259 OID 43269)
-- Name: reconciliation_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reconciliation_items (
    id uuid NOT NULL,
    reconciliation_id uuid NOT NULL,
    transaction_id uuid,
    statement_date date NOT NULL,
    statement_description character varying(255),
    statement_amount numeric(15,2) NOT NULL,
    is_matched boolean,
    match_confidence numeric(5,4),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- TOC entry 241 (class 1259 OID 43247)
-- Name: reconciliation_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reconciliation_records (
    id uuid NOT NULL,
    account_id uuid NOT NULL,
    reconciliation_date date NOT NULL,
    statement_balance numeric(15,2),
    book_balance numeric(15,2),
    adjusted_balance numeric(15,2),
    status character varying(20) NOT NULL,
    reconciled_by uuid,
    discrepancy_amount numeric(15,2),
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- TOC entry 227 (class 1259 OID 42811)
-- Name: reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reports (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    report_type character varying(50) NOT NULL,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    fiscal_year integer,
    fiscal_quarter integer,
    is_business_report boolean NOT NULL,
    is_tax_report boolean NOT NULL,
    is_preliminary boolean NOT NULL,
    generation_status character varying(20),
    generated_at timestamp with time zone,
    generation_duration_ms integer,
    report_data jsonb NOT NULL,
    summary_metrics jsonb,
    chart_data jsonb,
    file_path character varying(500),
    file_format character varying(20),
    file_size_bytes integer,
    template_id character varying(100),
    filters jsonb,
    groupings jsonb,
    is_shared boolean,
    share_token character varying(255),
    share_expires_at timestamp with time zone,
    access_level character varying(20),
    version integer NOT NULL,
    parent_report_id uuid,
    is_archived boolean,
    error_code character varying(50),
    error_message text,
    tags jsonb,
    metadata jsonb,
    CONSTRAINT ck_access_level CHECK (((access_level)::text = ANY ((ARRAY['private'::character varying, 'shared'::character varying, 'public'::character varying])::text[]))),
    CONSTRAINT ck_file_format CHECK (((file_format)::text = ANY ((ARRAY['json'::character varying, 'pdf'::character varying, 'excel'::character varying, 'csv'::character varying, 'html'::character varying])::text[]))),
    CONSTRAINT ck_fiscal_quarter CHECK (((fiscal_quarter >= 1) AND (fiscal_quarter <= 4))),
    CONSTRAINT ck_generation_status CHECK (((generation_status)::text = ANY ((ARRAY['pending'::character varying, 'generating'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::text[]))),
    CONSTRAINT ck_positive_version CHECK ((version > 0)),
    CONSTRAINT ck_report_type CHECK (((report_type)::text = ANY ((ARRAY['profit_loss'::character varying, 'balance_sheet'::character varying, 'cash_flow'::character varying, 'owner_package'::character varying, 'tax_summary'::character varying, 'budget_vs_actual'::character varying, 'expense_analysis'::character varying, 'income_analysis'::character varying, 'custom'::character varying])::text[]))),
    CONSTRAINT ck_valid_period CHECK ((period_end >= period_start))
);


--
-- TOC entry 233 (class 1259 OID 42992)
-- Name: tax_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tax_categories (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    category_code character varying(20) NOT NULL,
    category_name character varying(255) NOT NULL,
    tax_form character varying(50) NOT NULL,
    tax_line character varying(100),
    description text,
    deduction_type character varying(50),
    percentage_limit numeric(5,2),
    dollar_limit numeric(15,2),
    carryover_allowed boolean,
    documentation_required boolean,
    is_business_expense boolean,
    is_active boolean,
    effective_date date NOT NULL,
    expiration_date date,
    irs_reference character varying(100),
    keywords jsonb,
    exclusions jsonb,
    special_rules jsonb,
    CONSTRAINT ck_deduction_type CHECK (((deduction_type)::text = ANY ((ARRAY['ordinary'::character varying, 'capital'::character varying, 'itemized'::character varying, 'above_line'::character varying, 'business'::character varying])::text[]))),
    CONSTRAINT ck_tax_form CHECK (((tax_form)::text = ANY ((ARRAY['Schedule C'::character varying, 'Schedule E'::character varying, 'Form 8829'::character varying, 'Form 4562'::character varying, 'Schedule A'::character varying])::text[])))
);


--
-- TOC entry 243 (class 1259 OID 43287)
-- Name: transaction_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction_patterns (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    pattern_type character varying(50) NOT NULL,
    pattern_data jsonb NOT NULL,
    confidence_score numeric(5,4) NOT NULL,
    last_occurrence date,
    next_expected date,
    is_active boolean,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- TOC entry 224 (class 1259 OID 42714)
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    account_id uuid NOT NULL,
    plaid_transaction_id character varying(255),
    amount numeric(15,2) NOT NULL,
    transaction_type character varying(10),
    date timestamp with time zone NOT NULL,
    posted_date timestamp with time zone,
    name character varying(500) NOT NULL,
    merchant_name character varying(255),
    description text,
    is_recurring boolean,
    is_transfer boolean,
    is_fee boolean,
    category_id uuid,
    subcategory character varying(100),
    user_category_override character varying(100),
    is_business boolean,
    is_tax_deductible boolean,
    tax_year integer,
    location_address character varying(500),
    location_city character varying(100),
    location_region character varying(100),
    location_postal_code character varying(20),
    location_country character varying(3),
    location_coordinates jsonb,
    payment_method character varying(50),
    payment_channel character varying(50),
    account_number_masked character varying(20),
    contra_transaction_id uuid,
    journal_entry_id uuid,
    is_reconciled boolean NOT NULL,
    reconciled_date timestamp with time zone,
    reconciled_by character varying(255),
    notes text,
    tags jsonb,
    attachments jsonb,
    plaid_metadata jsonb,
    processing_status character varying(20),
    error_details text,
    chart_account_id uuid,
    tax_category_id uuid,
    schedule_c_line character varying(50),
    business_use_percentage numeric(5,2),
    deductible_amount numeric(15,2),
    requires_substantiation boolean,
    substantiation_complete boolean,
    tax_notes text,
    iso_currency_code character varying(3) DEFAULT 'USD'::character varying,
    datetime timestamp with time zone,
    authorized_date date,
    authorized_datetime timestamp with time zone,
    original_description text,
    plaid_category jsonb,
    plaid_category_id character varying(50),
    pending boolean DEFAULT false,
    pending_transaction_id character varying(255),
    transaction_code character varying(50),
    location jsonb,
    account_owner character varying(255),
    logo_url text,
    website character varying(500),
    payment_meta jsonb,
    CONSTRAINT ck_business_use_percentage CHECK (((business_use_percentage >= (0)::numeric) AND (business_use_percentage <= (100)::numeric))),
    CONSTRAINT ck_processing_status CHECK (((processing_status)::text = ANY ((ARRAY['processed'::character varying, 'pending'::character varying, 'error'::character varying, 'manual_review'::character varying])::text[]))),
    CONSTRAINT ck_transaction_type CHECK (((transaction_type)::text = ANY ((ARRAY['debit'::character varying, 'credit'::character varying])::text[])))
);


--
-- TOC entry 223 (class 1259 OID 42687)
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_sessions (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    session_token character varying(255) NOT NULL,
    refresh_token character varying(255),
    device_info jsonb,
    user_agent character varying(500),
    ip_address inet,
    location_info jsonb,
    expires_at timestamp with time zone NOT NULL,
    last_activity timestamp with time zone NOT NULL,
    login_time timestamp with time zone NOT NULL,
    is_active boolean NOT NULL,
    logout_time timestamp with time zone,
    logout_reason character varying(50),
    is_suspicious boolean,
    risk_score integer,
    requires_mfa boolean,
    mfa_verified boolean,
    session_type character varying(20),
    login_method character varying(50),
    metadata jsonb,
    CONSTRAINT ck_logout_reason CHECK (((logout_reason)::text = ANY ((ARRAY['user_logout'::character varying, 'timeout'::character varying, 'security'::character varying, 'admin'::character varying, 'expired'::character varying])::text[]))),
    CONSTRAINT ck_risk_score_range CHECK (((risk_score >= 0) AND (risk_score <= 100))),
    CONSTRAINT ck_session_type CHECK (((session_type)::text = ANY ((ARRAY['web'::character varying, 'mobile'::character varying, 'api'::character varying, 'background'::character varying])::text[]))),
    CONSTRAINT ck_valid_expiry CHECK ((expires_at > created_at))
);


--
-- TOC entry 218 (class 1259 OID 42584)
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(255),
    is_active boolean NOT NULL,
    is_superuser boolean NOT NULL,
    is_verified boolean NOT NULL,
    email_verified_at timestamp with time zone,
    first_name character varying(100),
    last_name character varying(100),
    phone character varying(20),
    timezone character varying(50),
    business_name character varying(255),
    business_type character varying(100),
    tax_id character varying(20),
    business_address jsonb,
    preferences jsonb,
    notification_settings jsonb,
    last_login timestamp with time zone,
    failed_login_attempts character varying(10),
    account_locked_until timestamp with time zone,
    password_reset_token character varying(255),
    password_reset_expires timestamp with time zone
);


--
-- TOC entry 4155 (class 0 OID 43155)
-- Dependencies: 237
-- Data for Name: accounting_periods; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4140 (class 0 OID 42653)
-- Dependencies: 222
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('c123321a-1ca7-48d2-8fcc-e1975d905129', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'aaVAelp4yqUKEAzBPe5ohB8bQ5V3KDtZ5K4xz', NULL, 'Plaid Checking', 'Plaid Gold Standard 0% Interest Checking', 'depository', 'checking', false, true, false, 110.00, 100.00, NULL, NULL, '0000', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('99796aa2-ef1d-445c-8538-ef9861485756', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', '4Q84rPLBjWH56pNBex87Tg7n6Rq4pvcJbR5ww', NULL, 'Plaid Saving', 'Plaid Silver Standard 0.1% Interest Saving', 'depository', 'savings', false, true, false, 210.00, 200.00, NULL, NULL, '1111', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('59d960d8-7cd1-4b24-83e4-e32aa1d09678', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'NQ1dR9KmbZHwLWPvGKoVIqD6bZaGBpTy6AZqm', NULL, 'Plaid CD', 'Plaid Bronze Standard 0.2% Interest CD', 'depository', 'cd', false, true, false, 1000.00, NULL, NULL, NULL, '2222', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'PMp4bwz9X1ubdlMB1JnXS9jV4dax6pFo6ydrW', NULL, 'Plaid Credit Card', 'Plaid Diamond 12.5% APR Interest Credit Card', 'credit', 'credit card', false, true, false, 410.00, NULL, 2000.00, NULL, '3333', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('314e3c17-c1d4-4c71-8890-dd60ee61b120', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'jMVdbaE1X4u9xyDjr5bNHVP3vEekaAi6WR48A', NULL, 'Plaid Money Market', 'Plaid Platinum Standard 1.85% Interest Money Market', 'depository', 'money market', false, true, false, 43200.00, 43200.00, NULL, NULL, '4444', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('959f8d38-7da6-4f2a-a0b8-a26e0c2a4fd2', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', '71Ajpeqd3nuvPX7azZ8RCJRvdrAGqBudJBQKx', NULL, 'Plaid IRA', NULL, 'investment', 'ira', false, true, false, 320.76, NULL, NULL, NULL, '5555', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('36625a9e-e791-4a7d-b83b-eb9a3f412582', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'ejVrvzE7QBsGM5dx6yoAI4Djx3boJ5Cr93Dl3', NULL, 'Plaid 401k', NULL, 'investment', '401k', false, true, false, 23631.98, NULL, NULL, NULL, '6666', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('d74197ad-1f91-4136-a9b5-6bbbcc10762c', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'Q1oNJkBvgLueEqA1bdnJS5dbXolygxcwmloWP', NULL, 'Plaid Student Loan', NULL, 'loan', 'student', false, true, false, 65262.00, NULL, NULL, NULL, '7777', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('a7d1552d-36d0-4e8a-9dd5-aed63fb68b5b', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'ZKVLqJ7rDnHka4A5r1nXsBbXmL5Z6zteq1LDm', NULL, 'Plaid Mortgage', NULL, 'loan', 'mortgage', false, true, false, 56302.06, NULL, NULL, NULL, '8888', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('a4f0eeb6-6dc2-4b37-be01-004cf2b45366', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'MeMx7mqbGQI94WNyd6pZH1NDMxAE7pHL6Rx86', NULL, 'Plaid HSA', 'Plaid Cares Health Savings Account', 'depository', 'hsa', false, true, false, 6009.00, 6009.00, NULL, NULL, '9001', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('1d4b8e73-3146-42fb-a54e-d535c3819350', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', '1jpxlaZK3gs7MeXK3dQvsQB1zj3wNWipjP7Gd', NULL, 'Plaid Cash Management', 'Plaid Growth Cash Management', 'depository', 'cash management', false, true, false, 12060.00, 12060.00, NULL, NULL, '9002', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');
INSERT INTO public.accounts (id, created_at, updated_at, user_id, institution_id, plaid_item_id, plaid_account_id, plaid_persistent_id, name, official_name, account_type, account_subtype, is_business, is_active, is_manual, current_balance, available_balance, credit_limit, minimum_balance, account_number_masked, routing_number, last_sync, sync_status, error_code, error_message, metadata, iso_currency_code) VALUES ('44c058b0-087e-4ac6-87dc-9ed02d0159c3', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', '4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', 'L7Z3V9lnyeTbNnM3aDLwSGP9q8rxLKCkjW8yX', NULL, 'Plaid Business Credit Card', 'Plaid Platinum Small Business Credit Card', 'credit', 'credit card', false, true, false, 5020.00, 4980.00, 10000.00, NULL, '9999', NULL, NULL, NULL, NULL, NULL, NULL, 'USD');


--
-- TOC entry 4135 (class 0 OID 42579)
-- Dependencies: 217
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.alembic_version (version_num) VALUES ('008');


--
-- TOC entry 4149 (class 0 OID 42931)
-- Dependencies: 231
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4156 (class 0 OID 43170)
-- Dependencies: 238
-- Data for Name: bookkeeping_rules; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4147 (class 0 OID 42872)
-- Dependencies: 229
-- Data for Name: budget_items; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4146 (class 0 OID 42847)
-- Dependencies: 228
-- Data for Name: budgets; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4152 (class 0 OID 43009)
-- Dependencies: 234
-- Data for Name: business_expense_tracking; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4138 (class 0 OID 42609)
-- Dependencies: 220
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('d1ec4a70-9f5c-4955-be3c-d153892116ad', '2025-09-19 11:58:05.593947-07', '2025-09-19 11:58:05.59395-07', NULL, 'Sales Revenue', 'Income', 'Revenue from product sales', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('8dccbe38-b4c6-49ca-a444-70b4f1d4a1c0', '2025-09-19 11:58:05.595193-07', '2025-09-19 11:58:05.595194-07', NULL, 'Service Revenue', 'Income', 'Revenue from services', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('257e8cc6-a713-44c3-ae80-1b09a889f377', '2025-09-19 11:58:05.595543-07', '2025-09-19 11:58:05.595544-07', NULL, 'Consulting Revenue', 'Income', 'Revenue from consulting', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('f42b0de2-a6cd-4f6d-8039-29d835e3bb41', '2025-09-19 11:58:05.595864-07', '2025-09-19 11:58:05.595865-07', NULL, 'Investment Income', 'Income', 'Income from investments', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('e70e3b78-4e3f-48de-80db-75569c42b2ae', '2025-09-19 11:58:05.596154-07', '2025-09-19 11:58:05.596155-07', NULL, 'Interest Income', 'Income', 'Interest earned', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('e0795cb9-1e5a-4f9d-be5d-4c75b4dc033b', '2025-09-19 11:58:05.596373-07', '2025-09-19 11:58:05.596373-07', NULL, 'Other Income', 'Income', 'Miscellaneous income', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('dece2818-82bd-479a-874d-b911bc95af3d', '2025-09-19 11:58:05.596727-07', '2025-09-19 11:58:05.596728-07', NULL, 'Office Supplies', 'Expense', 'Office supplies and materials', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('905d48a4-7279-403d-a16e-f20b7b3a2ac9', '2025-09-19 11:58:05.59694-07', '2025-09-19 11:58:05.59694-07', NULL, 'Software & Subscriptions', 'Expense', 'Software licenses and subscriptions', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('6dd48219-6d5a-4d18-bb65-af35255162ca', '2025-09-19 11:58:05.597182-07', '2025-09-19 11:58:05.597183-07', NULL, 'Professional Services', 'Expense', 'Legal, accounting, consulting', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('da9870f4-88c1-470a-bb3c-39f1d82782fb', '2025-09-19 11:58:05.597406-07', '2025-09-19 11:58:05.597406-07', NULL, 'Marketing & Advertising', 'Expense', 'Marketing and advertising costs', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('a3de5d99-2db5-43f2-8849-f834a1a4ee84', '2025-09-19 11:58:05.59761-07', '2025-09-19 11:58:05.59761-07', NULL, 'Travel - Business', 'Expense', 'Business travel expenses', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('2742dc07-ab16-4494-9a63-2a8f4c8d7ea6', '2025-09-19 11:58:05.597809-07', '2025-09-19 11:58:05.59781-07', NULL, 'Meals & Entertainment', 'Expense', 'Business meals and entertainment', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('bdaca2ca-3e01-45f9-8490-5d1d0d080efb', '2025-09-19 11:58:05.598005-07', '2025-09-19 11:58:05.598005-07', NULL, 'Equipment', 'Expense', 'Business equipment and tools', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('c78f11fa-3be9-4b9c-99ae-71e312a86330', '2025-09-19 11:58:05.598481-07', '2025-09-19 11:58:05.598481-07', NULL, 'Insurance', 'Expense', 'Business insurance premiums', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('f47802a2-eee9-4bba-80fa-2262cd8a896a', '2025-09-19 11:58:05.598871-07', '2025-09-19 11:58:05.598871-07', NULL, 'Rent & Utilities', 'Expense', 'Office rent and utilities', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('ba33a754-0716-4807-8567-7fceaefdccb7', '2025-09-19 11:58:05.599127-07', '2025-09-19 11:58:05.599128-07', NULL, 'Payroll', 'Expense', 'Employee salaries and wages', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('45145ec1-363c-44af-a641-cc29a4300a45', '2025-09-19 11:58:05.599373-07', '2025-09-19 11:58:05.599374-07', NULL, 'Contractor Payments', 'Expense', 'Payments to contractors', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('edd5ed72-2178-40ee-954f-67c875e1de4e', '2025-09-19 11:58:05.599758-07', '2025-09-19 11:58:05.599758-07', NULL, 'Bank Fees', 'Expense', 'Banking and financial fees', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('dadb45a8-f877-4b01-a074-2aba9e6c5f87', '2025-09-19 11:58:05.600019-07', '2025-09-19 11:58:05.600019-07', NULL, 'Food & Dining', 'Expense', 'Personal meals and restaurants', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('cc1a8c95-0892-4ac3-8103-1c38b40e6538', '2025-09-19 11:58:05.600304-07', '2025-09-19 11:58:05.600304-07', NULL, 'Transportation', 'Expense', 'Personal transportation costs', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('12c1d399-b447-4b37-8602-749c40720100', '2025-09-19 11:58:05.600605-07', '2025-09-19 11:58:05.600606-07', NULL, 'Shopping', 'Expense', 'Personal shopping and retail', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('5087745a-b39f-4ca6-a9dc-2995d870626a', '2025-09-19 11:58:05.60095-07', '2025-09-19 11:58:05.600951-07', NULL, 'Entertainment', 'Expense', 'Personal entertainment', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('381fcb4e-20b6-4fba-93d1-05c0af0fc96c', '2025-09-19 11:58:05.601299-07', '2025-09-19 11:58:05.601301-07', NULL, 'Healthcare', 'Expense', 'Medical and health expenses', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('d0e9bdad-a2bf-4a6c-a5ad-78a7a09d320b', '2025-09-19 11:58:05.601607-07', '2025-09-19 11:58:05.601608-07', NULL, 'Housing', 'Expense', 'Personal rent/mortgage', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('19e64fa2-1b80-48b7-a645-afd58db90389', '2025-09-19 11:58:05.60185-07', '2025-09-19 11:58:05.601851-07', NULL, 'Personal Care', 'Expense', 'Personal care and grooming', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('4e6edcb3-cadf-45ea-9fbe-220b55943303', '2025-09-19 11:58:05.602096-07', '2025-09-19 11:58:05.602096-07', NULL, 'Education', 'Expense', 'Education and learning', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('dec0323c-0778-4b54-a7cb-9a242648924d', '2025-09-19 11:58:05.602333-07', '2025-09-19 11:58:05.602334-07', NULL, 'Transfer In', 'Transfer', 'Money transferred in', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('4e931c10-7c25-407e-b5b7-50a9fb542696', '2025-09-19 11:58:05.602593-07', '2025-09-19 11:58:05.602593-07', NULL, 'Transfer Out', 'Transfer', 'Money transferred out', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('e8dd097c-0ec9-407a-ad29-c8d2c6cf465f', '2025-09-19 11:58:05.602904-07', '2025-09-19 11:58:05.602905-07', NULL, 'Credit Card Payment', 'Transfer', 'Credit card payments', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('7382733c-04de-40f9-ace5-c614229f9c33', '2025-09-19 11:58:05.603259-07', '2025-09-19 11:58:05.60326-07', NULL, 'Loan Payment', 'Other', 'Loan payments', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('0fc9ce97-6756-4d06-a932-5b1ab4b867e9', '2025-09-19 11:58:05.603599-07', '2025-09-19 11:58:05.6036-07', NULL, 'Owner Draw', 'Other', 'Owner withdrawals', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('4e612936-86a7-47a1-89e4-e3f8e86769d4', '2025-09-19 11:58:05.603978-07', '2025-09-19 11:58:05.603978-07', NULL, 'Owner Investment', 'Other', 'Owner capital contributions', NULL, NULL, true, true, NULL);
INSERT INTO public.categories (id, created_at, updated_at, user_id, name, parent_category, description, color, icon, is_system, is_active, rules) VALUES ('90301bba-2121-454c-9ef2-bb160a4ca4ea', '2025-09-19 11:58:05.604237-07', '2025-09-19 11:58:05.604238-07', NULL, 'Uncategorized', 'Other', 'Uncategorized transactions', NULL, NULL, true, true, NULL);


--
-- TOC entry 4154 (class 0 OID 43073)
-- Dependencies: 236
-- Data for Name: categorization_audit; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4144 (class 0 OID 42782)
-- Dependencies: 226
-- Data for Name: categorization_rules; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4153 (class 0 OID 43036)
-- Dependencies: 235
-- Data for Name: category_mappings; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('0774ea18-bc12-4c74-bea0-b2a5b852073d', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'dece2818-82bd-479a-874d-b911bc95af3d', 'a458dba3-aa2f-48a8-94e4-2bfeaf8ae762', 'd8a30f82-84a9-47e9-90a3-209ad53ef403', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('303b0b13-611a-4162-a743-b1f904880362', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '905d48a4-7279-403d-a16e-f20b7b3a2ac9', '87fcd58d-c945-4b1a-a4bf-81f15653a447', 'b858ee68-a4cf-455d-9451-cf141bb8f60a', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('7546136e-9552-4039-b4d7-600eafa285ce', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6dd48219-6d5a-4d18-bb65-af35255162ca', '7520dc97-0649-4a44-afbb-08181925d7f7', 'b05706ff-a974-4caf-8daa-d207f0c00420', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('d720b53b-92ed-43e4-9410-7bd0e2ba6a6e', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'da9870f4-88c1-470a-bb3c-39f1d82782fb', '3abde0f2-8b11-4e18-acb6-f5ecaab0d0c7', '2006f34d-124b-40e3-943c-d0cb176b679f', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('8f909938-c37f-4c53-92e4-4f794c1d17c2', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'a3de5d99-2db5-43f2-8849-f834a1a4ee84', 'fec6a52f-5db9-4c43-92a8-b36d0db45715', 'a5a1fc8a-d918-4f5f-a948-d7da4859c9b0', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('48e4ed80-6b98-41ec-8501-c519a5f90fd2', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2742dc07-ab16-4494-9a63-2a8f4c8d7ea6', 'fb15ecf5-120c-4a13-82d2-bac2c544b2f7', 'f4b7c3ef-1ee5-461b-9d81-054882679a99', 0.9500, false, true, '2024-01-01', NULL, 50.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('cc9bb49b-f112-4397-a763-b8e68fe8fca1', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bdaca2ca-3e01-45f9-8490-5d1d0d080efb', '649c08e0-e4d1-41cd-88c6-b0df1688e801', 'f9dce651-be7f-422c-885b-31f7b557047c', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('3f5de892-4ab9-4942-85a2-97be2a3c29da', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'c78f11fa-3be9-4b9c-99ae-71e312a86330', 'd9bef270-2c07-436d-9752-757329f23965', '9fa53a10-d417-4e7b-9409-185fd601c2f7', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('0a19670e-a61d-45c1-bcc7-a996f8462f5f', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'f47802a2-eee9-4bba-80fa-2262cd8a896a', 'a31524bb-5e72-4201-924b-ebdcdd7903cf', '2b41ecdf-2778-4d40-bf31-a9e7dc3f202c', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('2e62bafa-2b4e-41d7-b7a6-63aae5a6b10f', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'ba33a754-0716-4807-8567-7fceaefdccb7', '22ba36e1-3fe4-4599-ab2e-ac21ff641263', 'd6947eed-e702-42ca-88d1-2b6fe7fa0912', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('27c9caba-e432-4887-9549-40687ab038fe', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '45145ec1-363c-44af-a641-cc29a4300a45', 'd2588aa7-94a1-48a9-92e7-c576a9cbdbdf', '08ec5d5a-2af7-4bb8-865c-9b9a34a817b5', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('aa6a9484-536a-4491-9ece-c5d4ca9a4995', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'edd5ed72-2178-40ee-954f-67c875e1de4e', '87fcd58d-c945-4b1a-a4bf-81f15653a447', 'b858ee68-a4cf-455d-9451-cf141bb8f60a', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('6c37df1d-c9af-4e10-8434-5dca31f15d0c', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'cc1a8c95-0892-4ac3-8103-1c38b40e6538', 'a931c08d-18d2-4e02-91d4-768f2b6db4ef', '5c335f15-9431-4702-9c1b-222d2d7a9516', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);
INSERT INTO public.category_mappings (id, created_at, updated_at, user_id, source_category_id, chart_account_id, tax_category_id, confidence_score, is_user_defined, is_active, effective_date, expiration_date, business_percentage_default, always_require_receipt, auto_substantiation_rules, mapping_notes) VALUES ('f7a617dc-a778-47e4-b6c0-d39f45338ee7', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '4e6edcb3-cadf-45ea-9fbe-220b55943303', '87fcd58d-c945-4b1a-a4bf-81f15653a447', 'b858ee68-a4cf-455d-9451-cf141bb8f60a', 0.9500, false, true, '2024-01-01', NULL, 100.00, NULL, NULL, NULL);


--
-- TOC entry 4150 (class 0 OID 42965)
-- Dependencies: 232
-- Data for Name: chart_of_accounts; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('d057c1ad-a8e4-43e9-9a2e-a5c565519413', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1000', 'Cash and Cash Equivalents', 'asset', NULL, 'Operating cash accounts', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('f2616f49-42c4-4307-ac03-2d52e5049f56', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1010', 'Business Checking', 'asset', NULL, 'Primary business checking account', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('b543a1c6-a101-4a10-9832-8fcda48284b3', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1020', 'Business Savings', 'asset', NULL, 'Business savings account', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('2eb9c279-71e3-4122-9daf-da9d45115baf', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1100', 'Accounts Receivable', 'asset', NULL, 'Money owed by customers', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('73785c2b-ba02-42f9-804e-ef35818760fa', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1200', 'Inventory', 'asset', NULL, 'Products held for sale', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('da8c0bc6-0809-4893-a6df-ee4d4cec4371', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1500', 'Equipment', 'asset', NULL, 'Business equipment and machinery', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('34078646-e73d-4664-a863-563a98016447', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1510', 'Computer Equipment', 'asset', NULL, 'Computers and related equipment', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('c4bd070c-146d-401e-9b67-3b7ddb890032', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1520', 'Office Furniture', 'asset', NULL, 'Office furniture and fixtures', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('ec8e9261-d52c-42ef-89a8-3e2c8922fd90', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1600', 'Accumulated Depreciation', 'contra_asset', NULL, 'Accumulated depreciation on assets', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('212235a6-f394-4254-b871-a1c6a5a44f7f', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '1900', 'Other Assets', 'asset', NULL, 'Other business assets', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('fda149a6-2ccb-4465-83ee-bd8c83e45edc', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2000', 'Accounts Payable', 'liability', NULL, 'Money owed to vendors', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('7f0dd920-f066-4d5f-9722-69bbee900cb3', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2100', 'Credit Cards', 'liability', NULL, 'Business credit card balances', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('05a76914-a433-43e2-b25c-53fbb4f60462', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2200', 'Short-term Loans', 'liability', NULL, 'Loans due within one year', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('7d6126c0-74ab-499d-bbae-751e166e0121', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2300', 'Long-term Loans', 'liability', NULL, 'Loans due after one year', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('559ab6b7-6a2b-4c24-bacb-e2aababa1fb5', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2400', 'Sales Tax Payable', 'liability', NULL, 'Sales tax collected', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('64e8b043-39e9-4db1-ac9e-128834e7be2c', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2500', 'Payroll Liabilities', 'liability', NULL, 'Payroll taxes and withholdings', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('575036d1-5e3e-41c2-90d7-7e8ba0080110', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2600', 'Income Tax Payable', 'liability', NULL, 'Income tax owed', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('6bebb10b-e58e-489c-af6c-25c5aa1b8098', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '3000', 'Owner''s Equity', 'equity', NULL, 'Owner investment in business', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('6b74cad3-87af-439d-82e4-fb67b1d0be5e', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '3100', 'Owner''s Draw', 'equity', NULL, 'Owner withdrawals from business', 'debit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('0a8d1123-2fcd-4d92-90a4-90f4070e581f', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '3200', 'Retained Earnings', 'equity', NULL, 'Accumulated profits', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('810351b9-5656-4065-a013-4efa9115f2ea', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '4000', 'Service Revenue', 'revenue', NULL, 'Income from services', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('380b5c5d-4f5e-48ed-8771-a8b233a37ecf', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '4100', 'Product Sales', 'revenue', NULL, 'Income from product sales', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('310b903e-a695-4b35-94bc-12ec511231da', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '4200', 'Interest Income', 'revenue', NULL, 'Interest earned', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('20ad1a9d-0824-4f5c-93a6-f3c82bf43690', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '4900', 'Other Income', 'revenue', NULL, 'Miscellaneous income', 'credit', true, true, NULL, NULL, NULL, false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('3abde0f2-8b11-4e18-acb6-f5ecaab0d0c7', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5000', 'Advertising', 'expense', NULL, 'Marketing and advertising costs', 'debit', true, true, NULL, 'SCHED_C_8', 'SCHED_C_8', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('a931c08d-18d2-4e02-91d4-768f2b6db4ef', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5100', 'Vehicle Expenses', 'expense', NULL, 'Car and truck expenses', 'debit', true, true, NULL, 'SCHED_C_9', 'SCHED_C_9', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('f07fa8d9-4883-4c3b-8de2-1d1f538e5c3a', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5200', 'Commissions and Fees', 'expense', NULL, 'Commissions paid', 'debit', true, true, NULL, 'SCHED_C_10', 'SCHED_C_10', true, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('d2588aa7-94a1-48a9-92e7-c576a9cbdbdf', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5300', 'Contract Labor', 'expense', NULL, 'Independent contractor payments', 'debit', true, true, NULL, 'SCHED_C_11', 'SCHED_C_11', true, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('649c08e0-e4d1-41cd-88c6-b0df1688e801', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5400', 'Depreciation', 'expense', NULL, 'Asset depreciation', 'debit', true, true, NULL, 'SCHED_C_13', 'SCHED_C_13', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('d9bef270-2c07-436d-9752-757329f23965', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5500', 'Insurance', 'expense', NULL, 'Business insurance premiums', 'debit', true, true, NULL, 'SCHED_C_15', 'SCHED_C_15', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('2aecd5a3-337b-4513-b189-a9e6d274d181', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5600', 'Interest Expense', 'expense', NULL, 'Loan and credit interest', 'debit', true, true, NULL, 'SCHED_C_16B', 'SCHED_C_16B', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('7520dc97-0649-4a44-afbb-08181925d7f7', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5700', 'Legal and Professional', 'expense', NULL, 'Legal and professional fees', 'debit', true, true, NULL, 'SCHED_C_17', 'SCHED_C_17', true, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('a458dba3-aa2f-48a8-94e4-2bfeaf8ae762', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5800', 'Office Expenses', 'expense', NULL, 'Office supplies and expenses', 'debit', true, true, NULL, 'SCHED_C_18', 'SCHED_C_18', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('a31524bb-5e72-4201-924b-ebdcdd7903cf', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '5900', 'Rent', 'expense', NULL, 'Rent and lease payments', 'debit', true, true, NULL, 'SCHED_C_20B', 'SCHED_C_20B', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('36e38ac5-4e90-4ecd-bf1c-da861ce0df06', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6000', 'Repairs and Maintenance', 'expense', NULL, 'Repair and maintenance costs', 'debit', true, true, NULL, 'SCHED_C_21', 'SCHED_C_21', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('b06dad59-851f-47b6-943e-6f7a40e954cc', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6100', 'Supplies', 'expense', NULL, 'Business supplies', 'debit', true, true, NULL, 'SCHED_C_22', 'SCHED_C_22', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('f18bfc12-ba82-478d-a11a-1c5e77105f69', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6200', 'Taxes and Licenses', 'expense', NULL, 'Business taxes and licenses', 'debit', true, true, NULL, 'SCHED_C_23', 'SCHED_C_23', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('fec6a52f-5db9-4c43-92a8-b36d0db45715', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6300', 'Travel', 'expense', NULL, 'Business travel expenses', 'debit', true, true, NULL, 'SCHED_C_24A', 'SCHED_C_24A', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('fb15ecf5-120c-4a13-82d2-bac2c544b2f7', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6400', 'Meals', 'expense', NULL, 'Business meals (50% deductible)', 'debit', true, true, NULL, 'SCHED_C_24B', 'SCHED_C_24B', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('894b416f-e654-4ca7-8b68-c204de2a2c4a', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6500', 'Utilities', 'expense', NULL, 'Business utilities', 'debit', true, true, NULL, 'SCHED_C_25', 'SCHED_C_25', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('22ba36e1-3fe4-4599-ab2e-ac21ff641263', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6600', 'Wages', 'expense', NULL, 'Employee wages', 'debit', true, true, NULL, 'SCHED_C_26', 'SCHED_C_26', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('41764324-10b0-41cc-8957-abbf51227975', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6700', 'Bank Fees', 'expense', NULL, 'Bank service charges', 'debit', true, true, NULL, 'SCHED_C_27A', 'SCHED_C_27A', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('c68e800c-21e4-4d1c-8520-0c0d6ea482f2', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6800', 'Software Subscriptions', 'expense', NULL, 'Software and SaaS subscriptions', 'debit', true, true, NULL, 'SCHED_C_27A', 'SCHED_C_27A', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('15dd2d57-1141-44af-be39-e8aa27853d50', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '6900', 'Education and Training', 'expense', NULL, 'Professional development', 'debit', true, true, NULL, 'SCHED_C_27A', 'SCHED_C_27A', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('920fb31e-97b3-44a2-827a-cb3bb2b324ca', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '7000', 'Home Office', 'expense', NULL, 'Home office expenses', 'debit', true, true, NULL, 'FORM_8829', 'FORM_8829', false, NULL);
INSERT INTO public.chart_of_accounts (id, created_at, updated_at, user_id, account_code, account_name, account_type, parent_account_id, description, normal_balance, is_active, is_system_account, current_balance, tax_category, tax_line_mapping, requires_1099, account_metadata) VALUES ('87fcd58d-c945-4b1a-a4bf-81f15653a447', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', '8900', 'Other Expenses', 'expense', NULL, 'Other business expenses', 'debit', true, true, NULL, 'SCHED_C_27A', 'SCHED_C_27A', false, NULL);


--
-- TOC entry 4137 (class 0 OID 42597)
-- Dependencies: 219
-- Data for Name: institutions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.institutions (id, created_at, updated_at, plaid_institution_id, name, country_codes, products, routing_numbers, logo, primary_color, url, is_active, oauth_required, metadata) VALUES ('bab92faa-b38d-4784-b2d1-bbb421c61259', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:46:17.236346-07', 'ins_109509', 'First Gingham Credit Union', '["US"]', '["assets", "auth", "balance", "cra_lend_score", "cra_plaid_credit_score", "credit_details", "identity", "identity_match", "income", "income_verification", "investments", "liabilities", "pay_by_bank", "processor_payments", "recurring_transactions", "signal", "transactions", "transfer"]', '[]', NULL, NULL, NULL, true, false, '{}');


--
-- TOC entry 4157 (class 0 OID 43186)
-- Dependencies: 239
-- Data for Name: journal_entries; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4158 (class 0 OID 43216)
-- Dependencies: 240
-- Data for Name: journal_entry_lines; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4143 (class 0 OID 42754)
-- Dependencies: 225
-- Data for Name: ml_predictions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4139 (class 0 OID 42626)
-- Dependencies: 221
-- Data for Name: plaid_items; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.plaid_items (id, created_at, updated_at, user_id, institution_id, plaid_item_id, access_token, status, error_code, error_message, available_products, billed_products, webhook_url, consent_expiration_time, last_successful_sync, last_sync_attempt, cursor, max_days_back, sync_frequency_hours, is_active, requires_reauth, has_mfa, update_type, metadata, version) VALUES ('4a16f83d-5576-4de2-9f7e-c1ecf6dfafb2', '2025-09-19 13:46:17.236346-07', '2025-09-19 13:59:19.428127-07', 'a70ccf87-43a9-479d-82ee-f6b71fba23bb', 'bab92faa-b38d-4784-b2d1-bbb421c61259', 'p8V75ewEpQSEMV3n1eR4slmyXjEnB1CLeadAG', 'access-sandbox-236ba9bf-cd70-4f2e-8f4c-255033a54db5', 'active', NULL, NULL, '["assets", "auth", "balance", "identity_match", "income_verification", "investments", "liabilities", "recurring_transactions", "signal", "transfer"]', '["identity", "transactions"]', '', NULL, '2025-09-19 20:59:20.500205-07', '2025-09-19 20:59:19.43745-07', 'CAESJXFFVmVSUXdXcFpDV1B3eExEeU5qczFKUDVEVnA5emZnSzZtakUaDAiegrfGBhDw6aPMASIMCJ6Ct8YGEPDpo8wBKgwInoK3xgYQ8OmjzAE=', NULL, NULL, true, false, NULL, NULL, NULL, 1);


--
-- TOC entry 4148 (class 0 OID 42900)
-- Dependencies: 230
-- Data for Name: plaid_webhooks; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4160 (class 0 OID 43269)
-- Dependencies: 242
-- Data for Name: reconciliation_items; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4159 (class 0 OID 43247)
-- Dependencies: 241
-- Data for Name: reconciliation_records; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4145 (class 0 OID 42811)
-- Dependencies: 227
-- Data for Name: reports; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4151 (class 0 OID 42992)
-- Dependencies: 233
-- Data for Name: tax_categories; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('2006f34d-124b-40e3-943c-d0cb176b679f', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_8', 'Advertising', 'Schedule C', 'Line 8', 'Business advertising and promotional expenses', 'business', NULL, NULL, NULL, false, true, true, '2024-01-01', NULL, 'Pub 535', '["advertising", "marketing", "promotion", "ads", "social media ads", "google ads", "facebook ads"]', '["personal", "entertainment"]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('5c335f15-9431-4702-9c1b-222d2d7a9516', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_9', 'Car and truck expenses', 'Schedule C', 'Line 9', 'Vehicle expenses for business use', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 463', '["car", "truck", "vehicle", "gas", "fuel", "auto insurance", "repairs", "maintenance", "mileage"]', '[]', '{"mileage_rate_2024": "0.67", "mileage_rate_2025": "0.70", "requires_mileage_log": true, "business_use_percentage_required": true}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('a81757a7-d859-4c24-a206-765e3c4e72d7', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_10', 'Commissions and fees', 'Schedule C', 'Line 10', 'Commissions and fees paid to non-employees', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["commission", "fees", "referral", "finder", "broker", "affiliate"]', '[]', '{"requires_1099": true, "threshold_amount": "600.00"}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('08ec5d5a-2af7-4bb8-865c-9b9a34a817b5', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_11', 'Contract labor', 'Schedule C', 'Line 11', 'Payments to independent contractors', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["contractor", "freelancer", "consultant", "subcontractor", "1099"]', '[]', '{"requires_1099": true, "threshold_amount": "600.00"}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('f9dce651-be7f-422c-885b-31f7b557047c', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_13', 'Depreciation and section 179', 'Schedule C', 'Line 13', 'Depreciation of business property and Section 179 deduction', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 946', '["depreciation", "equipment", "furniture", "computers", "machinery", "section 179"]', '[]', '{"form_4562_required": true, "section_179_limit_2024": "1220000"}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('9fa53a10-d417-4e7b-9409-185fd601c2f7', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_15', 'Insurance', 'Schedule C', 'Line 15', 'Business insurance premiums (other than health)', 'business', NULL, NULL, NULL, false, true, true, '2024-01-01', NULL, 'Pub 535', '["insurance", "liability insurance", "property insurance", "business insurance", "errors omissions"]', '["health insurance", "life insurance"]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('c2e595ac-91bc-4b87-b8d6-38c69aaf366e', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_16A', 'Interest - Mortgage', 'Schedule C', 'Line 16a', 'Mortgage interest on business property', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["mortgage interest", "loan interest", "business mortgage"]', '[]', '{"form_1098_required": true}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('36b4549e-daea-45db-a339-6e4770b5d57c', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_16B', 'Interest - Other', 'Schedule C', 'Line 16b', 'Other business interest expenses', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["interest", "credit card interest", "loan interest", "line of credit"]', '[]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('b05706ff-a974-4caf-8daa-d207f0c00420', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_17', 'Legal and professional services', 'Schedule C', 'Line 17', 'Legal, accounting, and other professional fees', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["legal", "attorney", "lawyer", "accountant", "cpa", "bookkeeper", "professional services"]', '[]', '{"requires_1099": true, "threshold_amount": "600.00"}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('d8a30f82-84a9-47e9-90a3-209ad53ef403', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_18', 'Office expense', 'Schedule C', 'Line 18', 'General office supplies and expenses', 'business', NULL, NULL, NULL, false, true, true, '2024-01-01', NULL, 'Pub 535', '["office supplies", "paper", "pens", "printer ink", "toner", "staples", "folders"]', '["furniture", "equipment"]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('5920d70c-4685-49c3-866e-27795b27a5f4', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_20A', 'Rent or lease - Vehicles', 'Schedule C', 'Line 20a', 'Vehicle lease payments for business', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 463', '["vehicle lease", "car lease", "truck lease"]', '[]', '{"inclusion_amount_applies": true}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('2b41ecdf-2778-4d40-bf31-a9e7dc3f202c', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_20B', 'Rent or lease - Other', 'Schedule C', 'Line 20b', 'Office, equipment, and other business property rent', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["rent", "lease", "office rent", "equipment lease", "property lease"]', '[]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('f45bf8d9-7a98-4d04-b473-08f12e8adcaa', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_21', 'Repairs and maintenance', 'Schedule C', 'Line 21', 'Repairs and maintenance of business property', 'business', NULL, NULL, NULL, false, true, true, '2024-01-01', NULL, 'Pub 535', '["repairs", "maintenance", "fixing", "upkeep", "service"]', '["improvements", "capital expenses"]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('d576ff94-a4ac-470f-a522-a81e0a7177f5', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_22', 'Supplies', 'Schedule C', 'Line 22', 'Supplies consumed in business operations', 'business', NULL, NULL, NULL, false, true, true, '2024-01-01', NULL, 'Pub 535', '["supplies", "materials", "consumables", "inventory supplies"]', '["office supplies"]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('603c557d-28d9-4ff6-ae74-25c07e846a33', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_23', 'Taxes and licenses', 'Schedule C', 'Line 23', 'Business taxes and license fees', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["taxes", "licenses", "permits", "business license", "property tax", "sales tax"]', '["income tax", "self-employment tax"]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('a5a1fc8a-d918-4f5f-a948-d7da4859c9b0', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_24A', 'Travel', 'Schedule C', 'Line 24a', 'Business travel expenses', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 463', '["travel", "airfare", "hotel", "lodging", "taxi", "uber", "lyft", "train"]', '["commuting", "personal travel"]', '{"business_purpose_required": true}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('f4b7c3ef-1ee5-461b-9d81-054882679a99', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_24B', 'Meals', 'Schedule C', 'Line 24b', 'Business meals', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 463', '["meals", "dining", "restaurant", "food", "business meal", "client meal"]', '["entertainment", "personal meals"]', '{"deduction_percentage": "50", "temporary_100_percent_expired": "2022-12-31"}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('f16b94da-e312-426e-9309-ef82dfdc8f60', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_25', 'Utilities', 'Schedule C', 'Line 25', 'Business utilities', 'business', NULL, NULL, NULL, false, true, true, '2024-01-01', NULL, 'Pub 535', '["utilities", "electricity", "gas", "water", "phone", "internet", "cell phone"]', '[]', '{}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('d6947eed-e702-42ca-88d1-2b6fe7fa0912', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_26', 'Wages', 'Schedule C', 'Line 26', 'Wages paid to employees (W-2 wages)', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["wages", "salary", "payroll", "employee", "W-2"]', '["contractor payments", "1099 payments"]', '{"requires_w2": true, "payroll_tax_required": true}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('b858ee68-a4cf-455d-9451-cf141bb8f60a', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'SCHED_C_27A', 'Other expenses', 'Schedule C', 'Line 27a', 'Other ordinary and necessary business expenses', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 535', '["other", "miscellaneous", "bank fees", "software", "subscriptions", "education", "training"]', '[]', '{"requires_itemization": true}');
INSERT INTO public.tax_categories (id, created_at, updated_at, category_code, category_name, tax_form, tax_line, description, deduction_type, percentage_limit, dollar_limit, carryover_allowed, documentation_required, is_business_expense, is_active, effective_date, expiration_date, irs_reference, keywords, exclusions, special_rules) VALUES ('0299368e-0203-4e75-a873-93898badffc8', '2025-09-19 12:27:58.740414-07', '2025-09-19 12:27:58.740414-07', 'FORM_8829', 'Business use of home', 'Form 8829', 'Line 30', 'Home office deduction', 'business', NULL, NULL, NULL, true, true, true, '2024-01-01', NULL, 'Pub 587', '["home office", "business use of home", "home expenses"]', '[]', '{"simplified_max_sqft": "300", "simplified_rate_2024": "5.00", "exclusive_use_required": true, "principal_place_required": true, "simplified_method_available": true}');


--
-- TOC entry 4161 (class 0 OID 43287)
-- Dependencies: 243
-- Data for Name: transaction_patterns; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4142 (class 0 OID 42714)
-- Dependencies: 224
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('36533259-a3cf-40a5-9e14-7391c40732aa', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', '6MWPg7lxNGuB9bQVwG8Rtnabdqzz7kF8D5Ppz', 5.40, NULL, '2025-09-16 00:00:00-07', NULL, 'Uber 063015 SF**POOL**', 'Uber', NULL, NULL, NULL, NULL, NULL, 'Taxi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-15', NULL, NULL, '["Travel", "Taxi"]', '22016000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('0e5fc592-a288-4056-8a88-a97b42ae75c7', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'XlnM89PqEAHbJAMe6kmPSQm6E3AAgLSbKavNJ', -500.00, NULL, '2025-09-14 00:00:00-07', NULL, 'United Airlines', 'United Airlines', NULL, NULL, NULL, NULL, NULL, 'Airlines and Aviation Services', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-14', NULL, NULL, '["Travel", "Airlines and Aviation Services"]', '22001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('d1eb0d23-321a-46e6-bcbf-d43e2140f9bf', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'D3aW8v7pjkHEvWKkpnP7sVmvRA11eXu3WMLBG', 12.00, NULL, '2025-09-13 00:00:00-07', NULL, 'McDonald''s', 'McDonald''s', NULL, NULL, NULL, NULL, NULL, 'Fast Food', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-13', NULL, NULL, '["Food and Drink", "Restaurants", "Fast Food"]', '13005032', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": "3322"}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('70a6411a-4892-4dad-9dff-8d406dfc5086', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'V8AQW94VGESypADJ4vn6hL6XvZzzkWt9grZXA', 4.33, NULL, '2025-09-13 00:00:00-07', NULL, 'Starbucks', 'Starbucks', NULL, NULL, NULL, NULL, NULL, 'Coffee Shop', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-13', NULL, NULL, '["Food and Drink", "Restaurants", "Coffee Shop"]', '13005043', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('f352f418-c4e5-4d24-b38f-e4ba0955a5be', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'wBVpKoEy9kTGMo5PdBQbIZ1KAryybvFPZ81xD', 89.40, NULL, '2025-09-12 00:00:00-07', NULL, 'SparkFun', 'FUN', NULL, NULL, NULL, NULL, NULL, 'Restaurants', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-11', NULL, NULL, '["Food and Drink", "Restaurants"]', '13005000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('fe8fd3f2-24ef-4f52-b5f4-6318a1e373b1', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', '5ZENojp3GAHRM7Po6QkXCVaq4lWWdbu5KmQAa', 6.33, NULL, '2025-08-30 00:00:00-07', NULL, 'Uber 072515 SF**POOL**', 'Uber', NULL, NULL, NULL, NULL, NULL, 'Taxi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-29', NULL, NULL, '["Travel", "Taxi"]', '22016000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('99d452f6-faa0-4086-9791-c05fd9c397cd', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '99796aa2-ef1d-445c-8538-ef9861485756', 'JPezEmLARjSDNP9vjWM1i9VAEbqqjkUB6PevV', 25.00, NULL, '2025-09-16 00:00:00-07', NULL, 'CREDIT CARD 3333 PAYMENT *//', NULL, NULL, NULL, NULL, NULL, NULL, 'Credit Card', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-15', NULL, NULL, '["Payment", "Credit Card"]', '16001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('a6519b69-4db5-4321-8335-e6a1c926d61f', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '99796aa2-ef1d-445c-8538-ef9861485756', 'k15ay4ELjNu6kEq5DReLFlJQvoLLG7uL6v1eM', -4.22, NULL, '2025-09-11 00:00:00-07', NULL, 'INTRST PYMNT', NULL, NULL, NULL, NULL, NULL, NULL, 'Payroll', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-11', NULL, NULL, '["Transfer", "Payroll"]', '21009000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('c2132986-8370-4476-9ed5-8b48f8177acf', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '59d960d8-7cd1-4b24-83e4-e32aa1d09678', 'lLV4ZNEp5PsGbEKLwy9RIVxlyKzz5Bupoxme9', 1000.00, NULL, '2025-09-15 00:00:00-07', NULL, 'CD DEPOSIT .INITIAL.', NULL, NULL, NULL, NULL, NULL, NULL, 'Deposit', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Transfer", "Deposit"]', '21007000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('b81352f2-b097-4bb9-8ce3-18b37be7c4b0', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'qEVeRQwWpZCWPwxLDyNjs1JegwvvzjCgr3ykw', 78.50, NULL, '2025-09-14 00:00:00-07', NULL, 'Touchstone Climbing', NULL, NULL, NULL, NULL, NULL, NULL, 'Gyms and Fitness Centers', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-09-13', NULL, NULL, '["Recreation", "Gyms and Fitness Centers"]', '17018000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('594db791-9ed8-426f-b939-9fd9e65d563c', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'KjQBnmkG97spNjy8bm17uDPyVwll8GFRpQDbe', 500.00, NULL, '2025-09-01 00:00:00-07', NULL, 'United Airlines', 'United Airlines', NULL, NULL, NULL, NULL, NULL, 'Airlines and Aviation Services', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Travel", "Airlines and Aviation Services"]', '22001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('e69f98ba-77f8-42dd-869c-5a760a102d4d', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'rlVQJZEAyMHGPEdpb17XIE7b3NWWelh7JzkgE', 500.00, NULL, '2025-08-27 00:00:00-07', NULL, 'Tectra Inc', NULL, NULL, NULL, NULL, NULL, NULL, 'Restaurants', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Food and Drink", "Restaurants"]', '13005000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('ec0851d7-1c09-482f-952a-160817b74154', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'zdq8mbKRxWHMJbx1jnXghAgeR3ZZ58flNnXWz', 500.00, NULL, '2025-08-26 00:00:00-07', NULL, 'Madison Bicycle Shop', NULL, NULL, NULL, NULL, NULL, NULL, 'Sporting Goods', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Shops", "Sporting Goods"]', '19046000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('c025cf9a-f2cc-41cc-824d-ba0df1bd3adf', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'Bzx8RmP1dBHL6zykvK41sNGBkZaaJ4u4MlxnN', 500.00, NULL, '2025-08-26 00:00:00-07', NULL, 'KFC', 'KFC', NULL, NULL, NULL, NULL, NULL, 'Fast Food', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Food and Drink", "Restaurants", "Fast Food"]', '13005032', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('86b2eea2-05b9-4707-b98f-d0b14b974148', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', '3egaKN1zwEINad4lzm8nfwP39Nnn4oTZlxV33', 2078.50, NULL, '2025-08-26 00:00:00-07', NULL, 'AUTOMATIC PAYMENT - THANK', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Payment"]', '16000000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('42c6bc91-dd0f-4e3e-a49d-ed6b9dd202ec', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '314e3c17-c1d4-4c71-8890-dd60ee61b120', 'x3VorJl9w8HXMVL9njm5iemM8rXX3EU64bKvV', 5850.00, NULL, '2025-09-15 00:00:00-07', NULL, 'ACH Electronic CreditGUSTO PAY 123456', NULL, NULL, NULL, NULL, NULL, NULL, 'Debit', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Transfer", "Debit"]', '21006000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('0c5f96fe-51be-4fe5-bcee-72c52be41cab', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', '1jpxlaZK3gs7MeXK3dQvsQB86kmgbjSpdqKz7', 5.40, NULL, '2025-08-17 00:00:00-07', NULL, 'Uber 063015 SF**POOL**', 'Uber', NULL, NULL, NULL, NULL, NULL, 'Taxi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-16', NULL, NULL, '["Travel", "Taxi"]', '22016000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('cf51accb-cc0e-4612-8837-5cd8d6238c03', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'L7Z3V9lnyeTbNnM3aDLwSGPXenAgw8IkneQ7M', -500.00, NULL, '2025-08-15 00:00:00-07', NULL, 'United Airlines', 'United Airlines', NULL, NULL, NULL, NULL, NULL, 'Airlines and Aviation Services', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-15', NULL, NULL, '["Travel", "Airlines and Aviation Services"]', '22001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('d98ad8f8-b55d-4f04-a6d3-ad410891c451', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'p8V75ewEpQSEMV3n1eR4slmjqRrLPZipMJrwd', 12.00, NULL, '2025-08-14 00:00:00-07', NULL, 'McDonald''s', 'McDonald''s', NULL, NULL, NULL, NULL, NULL, 'Fast Food', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-14', NULL, NULL, '["Food and Drink", "Restaurants", "Fast Food"]', '13005032', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": "3322"}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('17a8a65f-d41b-4992-80e9-9b49eb368b6e', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'ogVj57E8NecGPEBdyob4I81KPmMZRdioepMjP', 4.33, NULL, '2025-08-14 00:00:00-07', NULL, 'Starbucks', 'Starbucks', NULL, NULL, NULL, NULL, NULL, 'Coffee Shop', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-14', NULL, NULL, '["Food and Drink", "Restaurants", "Coffee Shop"]', '13005043', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('620f25ea-5d88-46b1-af7a-4cad5bd3d5a8', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'geVBb39QZxIEMn4lzawdsv6w3N9RaotEpLVoZ', 89.40, NULL, '2025-08-13 00:00:00-07', NULL, 'SparkFun', 'FUN', NULL, NULL, NULL, NULL, NULL, 'Restaurants', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-12', NULL, NULL, '["Food and Drink", "Restaurants"]', '13005000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('a2d70f6a-c1d7-49ca-af18-bd8f1200f5cd', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', '8LG7pQKaVbswkJGjBRlMI9Wa8Pkw7JsWoZ1nv', 6.33, NULL, '2025-07-31 00:00:00-07', NULL, 'Uber 072515 SF**POOL**', 'Uber', NULL, NULL, NULL, NULL, NULL, 'Taxi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-30', NULL, NULL, '["Travel", "Taxi"]', '22016000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('a3e70c9f-00a3-4da1-baaf-86e452287c09', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'Ex4A96eoEdhkoxNdEKjLs1eXlDm53Bf4ngRyj', 5.40, NULL, '2025-07-18 00:00:00-07', NULL, 'Uber 063015 SF**POOL**', 'Uber', NULL, NULL, NULL, NULL, NULL, 'Taxi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-17', NULL, NULL, '["Travel", "Taxi"]', '22016000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('c0e618a0-4d08-4c30-98a0-02678a4e0bee', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'WEGZR9NlgWCkDxAlnGdbs75RPvVNxAi6zP9Rl', -500.00, NULL, '2025-07-16 00:00:00-07', NULL, 'United Airlines', 'United Airlines', NULL, NULL, NULL, NULL, NULL, 'Airlines and Aviation Services', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-16', NULL, NULL, '["Travel", "Airlines and Aviation Services"]', '22001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('0c3e26d7-47bf-4441-90a9-72d57672bc4a', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'Ar3gnmNMbzsKpr7Lv1amhe6MX3lKowu9N4j89', 12.00, NULL, '2025-07-15 00:00:00-07', NULL, 'McDonald''s', 'McDonald''s', NULL, NULL, NULL, NULL, NULL, 'Fast Food', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-15', NULL, NULL, '["Food and Drink", "Restaurants", "Fast Food"]', '13005032', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": "3322"}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('175a52e1-1b2f-4b6d-9f27-071baf42c2cf', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'GaPqQmZ8B4UK19QyGNe8hom9GJMDEaT6gGBaG', 4.33, NULL, '2025-07-15 00:00:00-07', NULL, 'Starbucks', 'Starbucks', NULL, NULL, NULL, NULL, NULL, 'Coffee Shop', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-15', NULL, NULL, '["Food and Drink", "Restaurants", "Coffee Shop"]', '13005043', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('dd356cae-00c3-43da-bee9-98dbc3e578dc', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'noVP5jEg17iG9yzNjxbQIlyVX3eJ5jiAq3eoK', 89.40, NULL, '2025-07-14 00:00:00-07', NULL, 'SparkFun', 'FUN', NULL, NULL, NULL, NULL, NULL, 'Restaurants', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-13', NULL, NULL, '["Food and Drink", "Restaurants"]', '13005000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('ca9816fa-4c15-4e2e-93b8-7d7cb4e2901e', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', 'c123321a-1ca7-48d2-8fcc-e1975d905129', 'b4VlxqENQKIGkEBm9a1rIX8EoQe3aZimpoxl3', 6.33, NULL, '2025-07-01 00:00:00-07', NULL, 'Uber 072515 SF**POOL**', 'Uber', NULL, NULL, NULL, NULL, NULL, 'Taxi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-06-30', NULL, NULL, '["Travel", "Taxi"]', '22016000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('b3a12283-d541-44a4-870e-8a7799eabdef', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '99796aa2-ef1d-445c-8538-ef9861485756', '9pne8Zr4NmSN57o63WqGfxbJaeVNryf4NqGrK', 25.00, NULL, '2025-08-17 00:00:00-07', NULL, 'CREDIT CARD 3333 PAYMENT *//', NULL, NULL, NULL, NULL, NULL, NULL, 'Credit Card', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-16', NULL, NULL, '["Payment", "Credit Card"]', '16001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('2349df2f-4187-447f-b03c-9bc8c06afde5', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '99796aa2-ef1d-445c-8538-ef9861485756', 'vzVLqkXm9oHEJ1Paow7rsE1RP9z3gMsqQvzpJ', -4.22, NULL, '2025-08-12 00:00:00-07', NULL, 'INTRST PYMNT', NULL, NULL, NULL, NULL, NULL, NULL, 'Payroll', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-12', NULL, NULL, '["Transfer", "Payroll"]', '21009000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('48b4b433-a2e0-4d83-8afd-f6aed0fbb562', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '99796aa2-ef1d-445c-8538-ef9861485756', 'RLgP893kXpsQ4KAWmLreTdy9PxEmKjfaVPl95', 25.00, NULL, '2025-07-18 00:00:00-07', NULL, 'CREDIT CARD 3333 PAYMENT *//', NULL, NULL, NULL, NULL, NULL, NULL, 'Credit Card', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-17', NULL, NULL, '["Payment", "Credit Card"]', '16001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('41cced21-96a0-4e8f-ae2b-550e9301dd56', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '99796aa2-ef1d-445c-8538-ef9861485756', '6MWPg7lxNGuB9bQVwG8RtnaVKGDl17C87196A', -4.22, NULL, '2025-07-13 00:00:00-07', NULL, 'INTRST PYMNT', NULL, NULL, NULL, NULL, NULL, NULL, 'Payroll', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-13', NULL, NULL, '["Transfer", "Payroll"]', '21009000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('5a21829e-fbca-4d03-a9ab-35dc8207f48b', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '59d960d8-7cd1-4b24-83e4-e32aa1d09678', 'D3aW8v7pjkHEvWKkpnP7sVm4oEWDket3q4w1A', 1000.00, NULL, '2025-08-16 00:00:00-07', NULL, 'CD DEPOSIT .INITIAL.', NULL, NULL, NULL, NULL, NULL, NULL, 'Deposit', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Transfer", "Deposit"]', '21007000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('0603fb37-5d01-4696-a3aa-32ff88b9a10e', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '59d960d8-7cd1-4b24-83e4-e32aa1d09678', 'V8AQW94VGESypADJ4vn6hL6pqPG85kC9Mqma3', 1000.00, NULL, '2025-07-17 00:00:00-07', NULL, 'CD DEPOSIT .INITIAL.', NULL, NULL, NULL, NULL, NULL, NULL, 'Deposit', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'other', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Transfer", "Deposit"]', '21007000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('60bbf5b8-8785-4ce2-a08d-cbf0051cc5ae', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'KjQBnmkG97spNjy8bm17uDPpELa5g8CRXEZ9a', 78.50, NULL, '2025-08-15 00:00:00-07', NULL, 'Touchstone Climbing', NULL, NULL, NULL, NULL, NULL, NULL, 'Gyms and Fitness Centers', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-08-14', NULL, NULL, '["Recreation", "Gyms and Fitness Centers"]', '17018000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('f7f105a1-c633-4bf7-8451-e248cd0d146f', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'rlVQJZEAyMHGPEdpb17XIE7rXpPJKes7RdPAg', 500.00, NULL, '2025-08-02 00:00:00-07', NULL, 'United Airlines', 'United Airlines', NULL, NULL, NULL, NULL, NULL, 'Airlines and Aviation Services', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Travel", "Airlines and Aviation Services"]', '22001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('f4ff6646-6c03-4037-b115-fc1b7932aa53', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'zdq8mbKRxWHMJbx1jnXghAgQKLPl45Clb37yL', 500.00, NULL, '2025-07-28 00:00:00-07', NULL, 'Tectra Inc', NULL, NULL, NULL, NULL, NULL, NULL, 'Restaurants', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Food and Drink", "Restaurants"]', '13005000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('5ca7eb5e-8a91-4337-9d3a-fa48089b8b26', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'Bzx8RmP1dBHL6zykvK41sNGygmXL7Jf4ozWpj', 500.00, NULL, '2025-07-27 00:00:00-07', NULL, 'Madison Bicycle Shop', NULL, NULL, NULL, NULL, NULL, NULL, 'Sporting Goods', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Shops", "Sporting Goods"]', '19046000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('992b3c89-2360-4800-8757-581530977041', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', '3egaKN1zwEINad4lzm8nfwPrkqlQX4IZymrjE', 500.00, NULL, '2025-07-27 00:00:00-07', NULL, 'KFC', 'KFC', NULL, NULL, NULL, NULL, NULL, 'Fast Food', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Food and Drink", "Restaurants", "Fast Food"]', '13005032', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('400d332c-adc4-4bab-af7d-84646528c7d0', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'x3VorJl9w8HXMVL9njm5iemLZN7W93u6ay7zK', 2078.50, NULL, '2025-07-27 00:00:00-07', NULL, 'AUTOMATIC PAYMENT - THANK', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Payment"]', '16000000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('13a9d9d2-9be7-4b18-b8b7-5df0d7b685b6', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'dPVKwrEjazSk5oxmN8vbsjyWBvlw8MiJ1BMby', 78.50, NULL, '2025-07-16 00:00:00-07', NULL, 'Touchstone Climbing', NULL, NULL, NULL, NULL, NULL, NULL, 'Gyms and Fitness Centers', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, '2025-07-15', NULL, NULL, '["Recreation", "Gyms and Fitness Centers"]', '17018000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('a5b471bb-c2ff-4df4-9401-770a2eee233f', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'aaVAelp4yqUKEAzBPe5ohB87kpAJe5fZmkaEJ', 500.00, NULL, '2025-07-03 00:00:00-07', NULL, 'United Airlines', 'United Airlines', NULL, NULL, NULL, NULL, NULL, 'Airlines and Aviation Services', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Travel", "Airlines and Aviation Services"]', '22001000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('7a956a3c-7757-410d-8b2f-89e4b6c3f009', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', '4Q84rPLBjWH56pNBex87Tg7QXAbWZRsJylrvb', 500.00, NULL, '2025-06-28 00:00:00-07', NULL, 'Tectra Inc', NULL, NULL, NULL, NULL, NULL, NULL, 'Restaurants', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Food and Drink", "Restaurants"]', '13005000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('f68da39c-6d77-49d9-a221-ce7b9002e475', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'NQ1dR9KmbZHwLWPvGKoVIqDeXvM58ZtyJXjGJ', 500.00, NULL, '2025-06-27 00:00:00-07', NULL, 'Madison Bicycle Shop', NULL, NULL, NULL, NULL, NULL, NULL, 'Sporting Goods', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Shops", "Sporting Goods"]', '19046000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('572c7bac-9b7f-45a9-af25-c8e0ba74f7f1', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'PMp4bwz9X1ubdlMB1JnXS9j1X8B5AdsolXkeP', 500.00, NULL, '2025-06-27 00:00:00-07', NULL, 'KFC', 'KFC', NULL, NULL, NULL, NULL, NULL, 'Fast Food', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'in store', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Food and Drink", "Restaurants", "Fast Food"]', '13005032', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('4a5526a4-3db3-4727-a645-4fff11aefcb5', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '84a2d7c0-dfbf-4538-ae5c-45ca5a5c2f92', 'jMVdbaE1X4u9xyDjr5bNHVP6j7MmlEt6gvM73', 2078.50, NULL, '2025-06-27 00:00:00-07', NULL, 'AUTOMATIC PAYMENT - THANK', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Payment"]', '16000000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('8a2e1121-2171-479c-80f1-27b29db8aaf5', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '314e3c17-c1d4-4c71-8890-dd60ee61b120', 'lLV4ZNEp5PsGbEKLwy9RIVxgNPwmW5tp3awqy', 5850.00, NULL, '2025-08-16 00:00:00-07', NULL, 'ACH Electronic CreditGUSTO PAY 123456', NULL, NULL, NULL, NULL, NULL, NULL, 'Debit', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Transfer", "Debit"]', '21006000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);
INSERT INTO public.transactions (id, created_at, updated_at, account_id, plaid_transaction_id, amount, transaction_type, date, posted_date, name, merchant_name, description, is_recurring, is_transfer, is_fee, category_id, subcategory, user_category_override, is_business, is_tax_deductible, tax_year, location_address, location_city, location_region, location_postal_code, location_country, location_coordinates, payment_method, payment_channel, account_number_masked, contra_transaction_id, journal_entry_id, is_reconciled, reconciled_date, reconciled_by, notes, tags, attachments, plaid_metadata, processing_status, error_details, chart_account_id, tax_category_id, schedule_c_line, business_use_percentage, deductible_amount, requires_substantiation, substantiation_complete, tax_notes, iso_currency_code, datetime, authorized_date, authorized_datetime, original_description, plaid_category, plaid_category_id, pending, pending_transaction_id, transaction_code, location, account_owner, logo_url, website, payment_meta) VALUES ('27e3c553-d7da-4b22-b817-73a1a068cafb', '2025-09-19 13:59:19.428127-07', '2025-09-19 13:59:19.428127-07', '314e3c17-c1d4-4c71-8890-dd60ee61b120', 'qEVeRQwWpZCWPwxLDyNjs1JP5DVp9zfgK6mjE', 5850.00, NULL, '2025-07-17 00:00:00-07', NULL, 'ACH Electronic CreditGUSTO PAY 123456', NULL, NULL, NULL, NULL, NULL, NULL, 'Debit', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'online', NULL, NULL, NULL, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'USD', NULL, NULL, NULL, NULL, '["Transfer", "Debit"]', '21006000', false, NULL, NULL, '{"lat": null, "lon": null, "city": null, "region": null, "address": null, "country": null, "postal_code": null, "store_number": null}', NULL, NULL, NULL, NULL);


--
-- TOC entry 4141 (class 0 OID 42687)
-- Dependencies: 223
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 4136 (class 0 OID 42584)
-- Dependencies: 218
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.users (id, created_at, updated_at, email, username, hashed_password, full_name, is_active, is_superuser, is_verified, email_verified_at, first_name, last_name, phone, timezone, business_name, business_type, tax_id, business_address, preferences, notification_settings, last_login, failed_login_attempts, account_locked_until, password_reset_token, password_reset_expires) VALUES ('a70ccf87-43a9-479d-82ee-f6b71fba23bb', '2025-09-19 11:58:05.591825-07', '2025-09-19 11:58:05.591828-07', 'isak@avidware.ai', 'isak', '$2b$12$ER2DVa348pAxaQ5wb0b1h.hwgCS/IM6uwt7UZoC4Wqw5nx0WYA3.u', 'Isak Demo User', true, false, true, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);


--
-- TOC entry 3902 (class 2606 OID 43161)
-- Name: accounting_periods accounting_periods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_periods
    ADD CONSTRAINT accounting_periods_pkey PRIMARY KEY (id);


--
-- TOC entry 3755 (class 2606 OID 42663)
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- TOC entry 3729 (class 2606 OID 42583)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3850 (class 2606 OID 42939)
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3907 (class 2606 OID 43178)
-- Name: bookkeeping_rules bookkeeping_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookkeeping_rules
    ADD CONSTRAINT bookkeeping_rules_pkey PRIMARY KEY (id);


--
-- TOC entry 3832 (class 2606 OID 42883)
-- Name: budget_items budget_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_items
    ADD CONSTRAINT budget_items_pkey PRIMARY KEY (id);


--
-- TOC entry 3823 (class 2606 OID 42859)
-- Name: budgets budgets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budgets_pkey PRIMARY KEY (id);


--
-- TOC entry 3881 (class 2606 OID 43020)
-- Name: business_expense_tracking business_expense_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_expense_tracking
    ADD CONSTRAINT business_expense_tracking_pkey PRIMARY KEY (id);


--
-- TOC entry 3742 (class 2606 OID 42617)
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- TOC entry 3896 (class 2606 OID 43081)
-- Name: categorization_audit categorization_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_pkey PRIMARY KEY (id);


--
-- TOC entry 3803 (class 2606 OID 42794)
-- Name: categorization_rules categorization_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_rules
    ADD CONSTRAINT categorization_rules_pkey PRIMARY KEY (id);


--
-- TOC entry 3888 (class 2606 OID 43046)
-- Name: category_mappings category_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_pkey PRIMARY KEY (id);


--
-- TOC entry 3865 (class 2606 OID 42975)
-- Name: chart_of_accounts chart_of_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_of_accounts
    ADD CONSTRAINT chart_of_accounts_pkey PRIMARY KEY (id);


--
-- TOC entry 3739 (class 2606 OID 42605)
-- Name: institutions institutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institutions
    ADD CONSTRAINT institutions_pkey PRIMARY KEY (id);


--
-- TOC entry 3915 (class 2606 OID 43196)
-- Name: journal_entries journal_entries_entry_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_entry_number_key UNIQUE (entry_number);


--
-- TOC entry 3917 (class 2606 OID 43194)
-- Name: journal_entries journal_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_pkey PRIMARY KEY (id);


--
-- TOC entry 3921 (class 2606 OID 43224)
-- Name: journal_entry_lines journal_entry_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_pkey PRIMARY KEY (id);


--
-- TOC entry 3801 (class 2606 OID 42765)
-- Name: ml_predictions ml_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_predictions
    ADD CONSTRAINT ml_predictions_pkey PRIMARY KEY (id);


--
-- TOC entry 3753 (class 2606 OID 42637)
-- Name: plaid_items plaid_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plaid_items
    ADD CONSTRAINT plaid_items_pkey PRIMARY KEY (id);


--
-- TOC entry 3848 (class 2606 OID 42912)
-- Name: plaid_webhooks plaid_webhooks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plaid_webhooks
    ADD CONSTRAINT plaid_webhooks_pkey PRIMARY KEY (id);


--
-- TOC entry 3930 (class 2606 OID 43274)
-- Name: reconciliation_items reconciliation_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation_items
    ADD CONSTRAINT reconciliation_items_pkey PRIMARY KEY (id);


--
-- TOC entry 3926 (class 2606 OID 43255)
-- Name: reconciliation_records reconciliation_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation_records
    ADD CONSTRAINT reconciliation_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3821 (class 2606 OID 42826)
-- Name: reports reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (id);


--
-- TOC entry 3877 (class 2606 OID 43002)
-- Name: tax_categories tax_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_categories
    ADD CONSTRAINT tax_categories_pkey PRIMARY KEY (id);


--
-- TOC entry 3934 (class 2606 OID 43295)
-- Name: transaction_patterns transaction_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_patterns
    ADD CONSTRAINT transaction_patterns_pkey PRIMARY KEY (id);


--
-- TOC entry 3793 (class 2606 OID 42725)
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 3838 (class 2606 OID 42885)
-- Name: budget_items uq_budget_category; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_items
    ADD CONSTRAINT uq_budget_category UNIQUE (budget_id, category_id);


--
-- TOC entry 3879 (class 2606 OID 43004)
-- Name: tax_categories uq_tax_category_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_categories
    ADD CONSTRAINT uq_tax_category_code UNIQUE (category_code);


--
-- TOC entry 3886 (class 2606 OID 43022)
-- Name: business_expense_tracking uq_transaction_business_expense; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_expense_tracking
    ADD CONSTRAINT uq_transaction_business_expense UNIQUE (transaction_id);


--
-- TOC entry 3871 (class 2606 OID 42977)
-- Name: chart_of_accounts uq_user_account_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_of_accounts
    ADD CONSTRAINT uq_user_account_code UNIQUE (user_id, account_code);


--
-- TOC entry 3763 (class 2606 OID 42665)
-- Name: accounts uq_user_account_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT uq_user_account_name UNIQUE (user_id, name);


--
-- TOC entry 3830 (class 2606 OID 42861)
-- Name: budgets uq_user_budget_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT uq_user_budget_period UNIQUE (user_id, name, period_start);


--
-- TOC entry 3745 (class 2606 OID 42619)
-- Name: categories uq_user_category; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT uq_user_category UNIQUE (user_id, name);


--
-- TOC entry 3894 (class 2606 OID 43048)
-- Name: category_mappings uq_user_category_mapping; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT uq_user_category_mapping UNIQUE (user_id, source_category_id, effective_date);


--
-- TOC entry 3774 (class 2606 OID 42699)
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 3735 (class 2606 OID 42592)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3756 (class 1259 OID 42681)
-- Name: idx_accounts_business; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accounts_business ON public.accounts USING btree (is_business, is_active);


--
-- TOC entry 3757 (class 1259 OID 42682)
-- Name: idx_accounts_sync_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accounts_sync_status ON public.accounts USING btree (sync_status, last_sync);


--
-- TOC entry 3758 (class 1259 OID 42683)
-- Name: idx_accounts_user_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_accounts_user_type ON public.accounts USING btree (user_id, account_type);


--
-- TOC entry 3851 (class 1259 OID 42950)
-- Name: idx_audit_logs_action_resource; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_action_resource ON public.audit_logs USING btree (action, resource_type);


--
-- TOC entry 3852 (class 1259 OID 42951)
-- Name: idx_audit_logs_business_impact; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_business_impact ON public.audit_logs USING btree (business_impact, event_timestamp);


--
-- TOC entry 3853 (class 1259 OID 42952)
-- Name: idx_audit_logs_compliance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_compliance ON public.audit_logs USING btree (compliance_relevant, event_timestamp);


--
-- TOC entry 3854 (class 1259 OID 42953)
-- Name: idx_audit_logs_financial; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_financial ON public.audit_logs USING btree (financial_impact, event_timestamp);


--
-- TOC entry 3855 (class 1259 OID 42954)
-- Name: idx_audit_logs_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_ip ON public.audit_logs USING btree (ip_address);


--
-- TOC entry 3856 (class 1259 OID 42955)
-- Name: idx_audit_logs_request; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_request ON public.audit_logs USING btree (request_id);


--
-- TOC entry 3857 (class 1259 OID 42956)
-- Name: idx_audit_logs_resource; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_resource ON public.audit_logs USING btree (resource_type, resource_id);


--
-- TOC entry 3858 (class 1259 OID 42957)
-- Name: idx_audit_logs_source_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_source_time ON public.audit_logs USING btree (source, event_timestamp);


--
-- TOC entry 3859 (class 1259 OID 42958)
-- Name: idx_audit_logs_user_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_user_time ON public.audit_logs USING btree (user_id, event_timestamp);


--
-- TOC entry 3833 (class 1259 OID 42896)
-- Name: idx_budget_items_budget; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_items_budget ON public.budget_items USING btree (budget_id);


--
-- TOC entry 3834 (class 1259 OID 42897)
-- Name: idx_budget_items_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_items_category ON public.budget_items USING btree (category_id);


--
-- TOC entry 3835 (class 1259 OID 42898)
-- Name: idx_budget_items_essential; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_items_essential ON public.budget_items USING btree (is_essential);


--
-- TOC entry 3836 (class 1259 OID 42899)
-- Name: idx_budget_items_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_items_type ON public.budget_items USING btree (item_type, is_fixed);


--
-- TOC entry 3824 (class 1259 OID 42867)
-- Name: idx_budgets_business; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budgets_business ON public.budgets USING btree (is_business_budget, user_id);


--
-- TOC entry 3825 (class 1259 OID 42868)
-- Name: idx_budgets_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budgets_period ON public.budgets USING btree (period_start, period_end);


--
-- TOC entry 3826 (class 1259 OID 42869)
-- Name: idx_budgets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budgets_status ON public.budgets USING btree (status, is_active);


--
-- TOC entry 3827 (class 1259 OID 42870)
-- Name: idx_budgets_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budgets_type ON public.budgets USING btree (budget_type, is_active);


--
-- TOC entry 3828 (class 1259 OID 42871)
-- Name: idx_budgets_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budgets_user_active ON public.budgets USING btree (user_id, is_active);


--
-- TOC entry 3882 (class 1259 OID 43035)
-- Name: idx_business_expense_receipt; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_expense_receipt ON public.business_expense_tracking USING btree (receipt_required, receipt_attached);


--
-- TOC entry 3883 (class 1259 OID 43033)
-- Name: idx_business_expense_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_expense_transaction ON public.business_expense_tracking USING btree (transaction_id);


--
-- TOC entry 3884 (class 1259 OID 43034)
-- Name: idx_business_expense_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_expense_user ON public.business_expense_tracking USING btree (user_id);


--
-- TOC entry 3743 (class 1259 OID 42625)
-- Name: idx_categories_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_categories_user_active ON public.categories USING btree (user_id, is_active);


--
-- TOC entry 3897 (class 1259 OID 43124)
-- Name: idx_categorization_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_categorization_audit_action ON public.categorization_audit USING btree (action_type, created_at);


--
-- TOC entry 3898 (class 1259 OID 43125)
-- Name: idx_categorization_audit_automated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_categorization_audit_automated ON public.categorization_audit USING btree (automated, created_at);


--
-- TOC entry 3899 (class 1259 OID 43122)
-- Name: idx_categorization_audit_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_categorization_audit_transaction ON public.categorization_audit USING btree (transaction_id);


--
-- TOC entry 3900 (class 1259 OID 43123)
-- Name: idx_categorization_audit_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_categorization_audit_user ON public.categorization_audit USING btree (user_id, created_at);


--
-- TOC entry 3889 (class 1259 OID 43072)
-- Name: idx_category_mappings_effective; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_mappings_effective ON public.category_mappings USING btree (effective_date, expiration_date);


--
-- TOC entry 3890 (class 1259 OID 43069)
-- Name: idx_category_mappings_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_mappings_source ON public.category_mappings USING btree (source_category_id, is_active);


--
-- TOC entry 3891 (class 1259 OID 43071)
-- Name: idx_category_mappings_tax; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_mappings_tax ON public.category_mappings USING btree (tax_category_id);


--
-- TOC entry 3892 (class 1259 OID 43070)
-- Name: idx_category_mappings_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_mappings_user ON public.category_mappings USING btree (user_id, is_active);


--
-- TOC entry 3866 (class 1259 OID 42988)
-- Name: idx_chart_of_accounts_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chart_of_accounts_code ON public.chart_of_accounts USING btree (account_code);


--
-- TOC entry 3867 (class 1259 OID 42991)
-- Name: idx_chart_of_accounts_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chart_of_accounts_parent ON public.chart_of_accounts USING btree (parent_account_id);


--
-- TOC entry 3868 (class 1259 OID 42989)
-- Name: idx_chart_of_accounts_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chart_of_accounts_type ON public.chart_of_accounts USING btree (account_type, is_active);


--
-- TOC entry 3869 (class 1259 OID 42990)
-- Name: idx_chart_of_accounts_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chart_of_accounts_user ON public.chart_of_accounts USING btree (user_id, is_active);


--
-- TOC entry 3736 (class 1259 OID 42606)
-- Name: idx_institutions_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_institutions_active ON public.institutions USING btree (is_active);


--
-- TOC entry 3737 (class 1259 OID 42607)
-- Name: idx_institutions_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_institutions_name ON public.institutions USING btree (name);


--
-- TOC entry 3794 (class 1259 OID 42776)
-- Name: idx_ml_predictions_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_predictions_confidence ON public.ml_predictions USING btree (confidence);


--
-- TOC entry 3795 (class 1259 OID 42777)
-- Name: idx_ml_predictions_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_predictions_date ON public.ml_predictions USING btree (prediction_date);


--
-- TOC entry 3796 (class 1259 OID 42778)
-- Name: idx_ml_predictions_feedback; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_predictions_feedback ON public.ml_predictions USING btree (user_feedback, is_accepted);


--
-- TOC entry 3797 (class 1259 OID 42779)
-- Name: idx_ml_predictions_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_predictions_model ON public.ml_predictions USING btree (model_version, model_type);


--
-- TOC entry 3798 (class 1259 OID 42780)
-- Name: idx_ml_predictions_review; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_predictions_review ON public.ml_predictions USING btree (requires_review, is_outlier);


--
-- TOC entry 3799 (class 1259 OID 42781)
-- Name: idx_ml_predictions_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_predictions_transaction ON public.ml_predictions USING btree (transaction_id);


--
-- TOC entry 3746 (class 1259 OID 42648)
-- Name: idx_plaid_items_institution; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plaid_items_institution ON public.plaid_items USING btree (institution_id);


--
-- TOC entry 3747 (class 1259 OID 42649)
-- Name: idx_plaid_items_reauth; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plaid_items_reauth ON public.plaid_items USING btree (requires_reauth, is_active);


--
-- TOC entry 3748 (class 1259 OID 42650)
-- Name: idx_plaid_items_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plaid_items_status ON public.plaid_items USING btree (status, last_sync_attempt);


--
-- TOC entry 3749 (class 1259 OID 42651)
-- Name: idx_plaid_items_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plaid_items_user ON public.plaid_items USING btree (user_id, is_active);


--
-- TOC entry 3750 (class 1259 OID 42964)
-- Name: idx_plaid_items_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plaid_items_version ON public.plaid_items USING btree (version);


--
-- TOC entry 3810 (class 1259 OID 42837)
-- Name: idx_reports_business; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_business ON public.reports USING btree (is_business_report, user_id);


--
-- TOC entry 3811 (class 1259 OID 42838)
-- Name: idx_reports_fiscal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_fiscal ON public.reports USING btree (fiscal_year, fiscal_quarter);


--
-- TOC entry 3812 (class 1259 OID 42839)
-- Name: idx_reports_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_period ON public.reports USING btree (period_start, period_end);


--
-- TOC entry 3813 (class 1259 OID 42840)
-- Name: idx_reports_shared; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_shared ON public.reports USING btree (is_shared, share_expires_at);


--
-- TOC entry 3814 (class 1259 OID 42841)
-- Name: idx_reports_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_status ON public.reports USING btree (generation_status, generated_at);


--
-- TOC entry 3815 (class 1259 OID 42842)
-- Name: idx_reports_user_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_user_type ON public.reports USING btree (user_id, report_type);


--
-- TOC entry 3816 (class 1259 OID 42843)
-- Name: idx_reports_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_version ON public.reports USING btree (parent_report_id, version);


--
-- TOC entry 3804 (class 1259 OID 42805)
-- Name: idx_rules_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rules_category ON public.categorization_rules USING btree (category_id);


--
-- TOC entry 3805 (class 1259 OID 42806)
-- Name: idx_rules_pattern; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rules_pattern ON public.categorization_rules USING btree (pattern);


--
-- TOC entry 3806 (class 1259 OID 42807)
-- Name: idx_rules_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rules_priority ON public.categorization_rules USING btree (priority, is_active);


--
-- TOC entry 3807 (class 1259 OID 42808)
-- Name: idx_rules_system; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rules_system ON public.categorization_rules USING btree (is_system_rule, is_active);


--
-- TOC entry 3808 (class 1259 OID 42809)
-- Name: idx_rules_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rules_type ON public.categorization_rules USING btree (rule_type, is_active);


--
-- TOC entry 3809 (class 1259 OID 42810)
-- Name: idx_rules_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rules_user_active ON public.categorization_rules USING btree (user_id, is_active);


--
-- TOC entry 3764 (class 1259 OID 42705)
-- Name: idx_sessions_activity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_activity ON public.user_sessions USING btree (last_activity, is_active);


--
-- TOC entry 3765 (class 1259 OID 42706)
-- Name: idx_sessions_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_expires ON public.user_sessions USING btree (expires_at, is_active);


--
-- TOC entry 3766 (class 1259 OID 42707)
-- Name: idx_sessions_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_ip ON public.user_sessions USING btree (ip_address);


--
-- TOC entry 3767 (class 1259 OID 42708)
-- Name: idx_sessions_mfa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_mfa ON public.user_sessions USING btree (requires_mfa, mfa_verified);


--
-- TOC entry 3768 (class 1259 OID 42709)
-- Name: idx_sessions_suspicious; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_suspicious ON public.user_sessions USING btree (is_suspicious, risk_score);


--
-- TOC entry 3769 (class 1259 OID 42710)
-- Name: idx_sessions_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_type ON public.user_sessions USING btree (session_type, login_method);


--
-- TOC entry 3770 (class 1259 OID 42711)
-- Name: idx_sessions_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_user_active ON public.user_sessions USING btree (user_id, is_active);


--
-- TOC entry 3872 (class 1259 OID 43007)
-- Name: idx_tax_categories_business; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tax_categories_business ON public.tax_categories USING btree (is_business_expense, is_active);


--
-- TOC entry 3873 (class 1259 OID 43005)
-- Name: idx_tax_categories_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tax_categories_code ON public.tax_categories USING btree (category_code);


--
-- TOC entry 3874 (class 1259 OID 43008)
-- Name: idx_tax_categories_effective; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tax_categories_effective ON public.tax_categories USING btree (effective_date, expiration_date);


--
-- TOC entry 3875 (class 1259 OID 43006)
-- Name: idx_tax_categories_form; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tax_categories_form ON public.tax_categories USING btree (tax_form, is_active);


--
-- TOC entry 3775 (class 1259 OID 42741)
-- Name: idx_transactions_account_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_account_date ON public.transactions USING btree (account_id, date);


--
-- TOC entry 3776 (class 1259 OID 42742)
-- Name: idx_transactions_amount; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_amount ON public.transactions USING btree (amount);


--
-- TOC entry 3777 (class 1259 OID 42743)
-- Name: idx_transactions_business_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_business_date ON public.transactions USING btree (is_business, date);


--
-- TOC entry 3778 (class 1259 OID 42744)
-- Name: idx_transactions_category_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_category_date ON public.transactions USING btree (category_id, date);


--
-- TOC entry 3779 (class 1259 OID 43136)
-- Name: idx_transactions_chart_account; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_chart_account ON public.transactions USING btree (chart_account_id);


--
-- TOC entry 3780 (class 1259 OID 43140)
-- Name: idx_transactions_deductible; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_deductible ON public.transactions USING btree (is_tax_deductible, tax_year, deductible_amount);


--
-- TOC entry 3781 (class 1259 OID 42745)
-- Name: idx_transactions_journal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_journal ON public.transactions USING btree (journal_entry_id);


--
-- TOC entry 3782 (class 1259 OID 42746)
-- Name: idx_transactions_merchant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_merchant ON public.transactions USING btree (merchant_name);


--
-- TOC entry 3783 (class 1259 OID 42748)
-- Name: idx_transactions_reconciled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_reconciled ON public.transactions USING btree (is_reconciled);


--
-- TOC entry 3784 (class 1259 OID 43138)
-- Name: idx_transactions_schedule_c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_schedule_c ON public.transactions USING btree (schedule_c_line);


--
-- TOC entry 3785 (class 1259 OID 43139)
-- Name: idx_transactions_substantiation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_substantiation ON public.transactions USING btree (requires_substantiation, substantiation_complete);


--
-- TOC entry 3786 (class 1259 OID 43137)
-- Name: idx_transactions_tax_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_tax_category ON public.transactions USING btree (tax_category_id);


--
-- TOC entry 3787 (class 1259 OID 42749)
-- Name: idx_transactions_tax_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_tax_year ON public.transactions USING btree (tax_year, is_tax_deductible);


--
-- TOC entry 3730 (class 1259 OID 42593)
-- Name: idx_users_email_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email_active ON public.users USING btree (email, is_active);


--
-- TOC entry 3731 (class 1259 OID 42594)
-- Name: idx_users_last_login; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_last_login ON public.users USING btree (last_login);


--
-- TOC entry 3839 (class 1259 OID 42923)
-- Name: idx_webhooks_duplicate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_webhooks_duplicate ON public.plaid_webhooks USING btree (is_duplicate, webhook_hash);


--
-- TOC entry 3840 (class 1259 OID 42924)
-- Name: idx_webhooks_environment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_webhooks_environment ON public.plaid_webhooks USING btree (plaid_environment);


--
-- TOC entry 3841 (class 1259 OID 42925)
-- Name: idx_webhooks_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_webhooks_item ON public.plaid_webhooks USING btree (plaid_item_id, received_at);


--
-- TOC entry 3842 (class 1259 OID 42926)
-- Name: idx_webhooks_retry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_webhooks_retry ON public.plaid_webhooks USING btree (retry_count, processing_status);


--
-- TOC entry 3843 (class 1259 OID 42927)
-- Name: idx_webhooks_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_webhooks_status ON public.plaid_webhooks USING btree (processing_status, received_at);


--
-- TOC entry 3844 (class 1259 OID 42928)
-- Name: idx_webhooks_type_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_webhooks_type_code ON public.plaid_webhooks USING btree (webhook_type, webhook_code);


--
-- TOC entry 3903 (class 1259 OID 43169)
-- Name: ix_accounting_periods_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_periods_end_date ON public.accounting_periods USING btree (end_date);


--
-- TOC entry 3904 (class 1259 OID 43168)
-- Name: ix_accounting_periods_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_periods_start_date ON public.accounting_periods USING btree (start_date);


--
-- TOC entry 3905 (class 1259 OID 43167)
-- Name: ix_accounting_periods_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_periods_user_id ON public.accounting_periods USING btree (user_id);


--
-- TOC entry 3759 (class 1259 OID 42684)
-- Name: ix_accounts_plaid_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_accounts_plaid_account_id ON public.accounts USING btree (plaid_account_id);


--
-- TOC entry 3760 (class 1259 OID 42685)
-- Name: ix_accounts_plaid_persistent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_accounts_plaid_persistent_id ON public.accounts USING btree (plaid_persistent_id);


--
-- TOC entry 3761 (class 1259 OID 42686)
-- Name: ix_accounts_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounts_user_id ON public.accounts USING btree (user_id);


--
-- TOC entry 3860 (class 1259 OID 42959)
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- TOC entry 3861 (class 1259 OID 42960)
-- Name: ix_audit_logs_event_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_event_timestamp ON public.audit_logs USING btree (event_timestamp);


--
-- TOC entry 3862 (class 1259 OID 42961)
-- Name: ix_audit_logs_resource_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_resource_type ON public.audit_logs USING btree (resource_type);


--
-- TOC entry 3863 (class 1259 OID 42962)
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- TOC entry 3908 (class 1259 OID 43185)
-- Name: ix_bookkeeping_rules_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookkeeping_rules_is_active ON public.bookkeeping_rules USING btree (is_active);


--
-- TOC entry 3909 (class 1259 OID 43184)
-- Name: ix_bookkeeping_rules_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookkeeping_rules_user_id ON public.bookkeeping_rules USING btree (user_id);


--
-- TOC entry 3740 (class 1259 OID 42608)
-- Name: ix_institutions_plaid_institution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_institutions_plaid_institution_id ON public.institutions USING btree (plaid_institution_id);


--
-- TOC entry 3910 (class 1259 OID 43213)
-- Name: ix_journal_entries_entry_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_entries_entry_date ON public.journal_entries USING btree (entry_date);


--
-- TOC entry 3911 (class 1259 OID 43215)
-- Name: ix_journal_entries_is_posted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_entries_is_posted ON public.journal_entries USING btree (is_posted);


--
-- TOC entry 3912 (class 1259 OID 43214)
-- Name: ix_journal_entries_period_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_entries_period_id ON public.journal_entries USING btree (period_id);


--
-- TOC entry 3913 (class 1259 OID 43212)
-- Name: ix_journal_entries_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_entries_user_id ON public.journal_entries USING btree (user_id);


--
-- TOC entry 3918 (class 1259 OID 43245)
-- Name: ix_journal_entry_lines_journal_entry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_entry_lines_journal_entry_id ON public.journal_entry_lines USING btree (journal_entry_id);


--
-- TOC entry 3919 (class 1259 OID 43246)
-- Name: ix_journal_entry_lines_transaction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_entry_lines_transaction_id ON public.journal_entry_lines USING btree (transaction_id);


--
-- TOC entry 3751 (class 1259 OID 42652)
-- Name: ix_plaid_items_plaid_item_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_plaid_items_plaid_item_id ON public.plaid_items USING btree (plaid_item_id);


--
-- TOC entry 3845 (class 1259 OID 42929)
-- Name: ix_plaid_webhooks_plaid_item_id_raw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plaid_webhooks_plaid_item_id_raw ON public.plaid_webhooks USING btree (plaid_item_id_raw);


--
-- TOC entry 3846 (class 1259 OID 42930)
-- Name: ix_plaid_webhooks_webhook_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_plaid_webhooks_webhook_hash ON public.plaid_webhooks USING btree (webhook_hash);


--
-- TOC entry 3927 (class 1259 OID 43286)
-- Name: ix_reconciliation_items_is_matched; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reconciliation_items_is_matched ON public.reconciliation_items USING btree (is_matched);


--
-- TOC entry 3928 (class 1259 OID 43285)
-- Name: ix_reconciliation_items_reconciliation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reconciliation_items_reconciliation_id ON public.reconciliation_items USING btree (reconciliation_id);


--
-- TOC entry 3922 (class 1259 OID 43266)
-- Name: ix_reconciliation_records_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reconciliation_records_account_id ON public.reconciliation_records USING btree (account_id);


--
-- TOC entry 3923 (class 1259 OID 43267)
-- Name: ix_reconciliation_records_reconciliation_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reconciliation_records_reconciliation_date ON public.reconciliation_records USING btree (reconciliation_date);


--
-- TOC entry 3924 (class 1259 OID 43268)
-- Name: ix_reconciliation_records_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reconciliation_records_status ON public.reconciliation_records USING btree (status);


--
-- TOC entry 3817 (class 1259 OID 42844)
-- Name: ix_reports_fiscal_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reports_fiscal_year ON public.reports USING btree (fiscal_year);


--
-- TOC entry 3818 (class 1259 OID 42845)
-- Name: ix_reports_share_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_reports_share_token ON public.reports USING btree (share_token);


--
-- TOC entry 3819 (class 1259 OID 42846)
-- Name: ix_reports_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reports_user_id ON public.reports USING btree (user_id);


--
-- TOC entry 3931 (class 1259 OID 43302)
-- Name: ix_transaction_patterns_pattern_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transaction_patterns_pattern_type ON public.transaction_patterns USING btree (pattern_type);


--
-- TOC entry 3932 (class 1259 OID 43301)
-- Name: ix_transaction_patterns_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transaction_patterns_user_id ON public.transaction_patterns USING btree (user_id);


--
-- TOC entry 3788 (class 1259 OID 42750)
-- Name: ix_transactions_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_account_id ON public.transactions USING btree (account_id);


--
-- TOC entry 3789 (class 1259 OID 42751)
-- Name: ix_transactions_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_date ON public.transactions USING btree (date);


--
-- TOC entry 3790 (class 1259 OID 42752)
-- Name: ix_transactions_is_business; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_is_business ON public.transactions USING btree (is_business);


--
-- TOC entry 3791 (class 1259 OID 42753)
-- Name: ix_transactions_plaid_transaction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_transactions_plaid_transaction_id ON public.transactions USING btree (plaid_transaction_id);


--
-- TOC entry 3771 (class 1259 OID 42712)
-- Name: ix_user_sessions_refresh_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_user_sessions_refresh_token ON public.user_sessions USING btree (refresh_token);


--
-- TOC entry 3772 (class 1259 OID 42713)
-- Name: ix_user_sessions_session_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_user_sessions_session_token ON public.user_sessions USING btree (session_token);


--
-- TOC entry 3732 (class 1259 OID 42595)
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- TOC entry 3733 (class 1259 OID 42596)
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- TOC entry 3976 (class 2606 OID 43162)
-- Name: accounting_periods accounting_periods_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_periods
    ADD CONSTRAINT accounting_periods_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3938 (class 2606 OID 42666)
-- Name: accounts accounts_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- TOC entry 3939 (class 2606 OID 42671)
-- Name: accounts accounts_plaid_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_plaid_item_id_fkey FOREIGN KEY (plaid_item_id) REFERENCES public.plaid_items(id);


--
-- TOC entry 3940 (class 2606 OID 42676)
-- Name: accounts accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3958 (class 2606 OID 42940)
-- Name: audit_logs audit_logs_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.user_sessions(id);


--
-- TOC entry 3959 (class 2606 OID 42945)
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3977 (class 2606 OID 43179)
-- Name: bookkeeping_rules bookkeeping_rules_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookkeeping_rules
    ADD CONSTRAINT bookkeeping_rules_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3954 (class 2606 OID 42886)
-- Name: budget_items budget_items_budget_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_items
    ADD CONSTRAINT budget_items_budget_id_fkey FOREIGN KEY (budget_id) REFERENCES public.budgets(id);


--
-- TOC entry 3955 (class 2606 OID 42891)
-- Name: budget_items budget_items_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_items
    ADD CONSTRAINT budget_items_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- TOC entry 3953 (class 2606 OID 42862)
-- Name: budgets budgets_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budgets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3962 (class 2606 OID 43023)
-- Name: business_expense_tracking business_expense_tracking_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_expense_tracking
    ADD CONSTRAINT business_expense_tracking_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id) ON DELETE CASCADE;


--
-- TOC entry 3963 (class 2606 OID 43028)
-- Name: business_expense_tracking business_expense_tracking_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_expense_tracking
    ADD CONSTRAINT business_expense_tracking_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3935 (class 2606 OID 42620)
-- Name: categories categories_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3968 (class 2606 OID 43082)
-- Name: categorization_audit categorization_audit_new_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_new_category_id_fkey FOREIGN KEY (new_category_id) REFERENCES public.categories(id);


--
-- TOC entry 3969 (class 2606 OID 43087)
-- Name: categorization_audit categorization_audit_new_chart_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_new_chart_account_id_fkey FOREIGN KEY (new_chart_account_id) REFERENCES public.chart_of_accounts(id);


--
-- TOC entry 3970 (class 2606 OID 43092)
-- Name: categorization_audit categorization_audit_new_tax_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_new_tax_category_id_fkey FOREIGN KEY (new_tax_category_id) REFERENCES public.tax_categories(id);


--
-- TOC entry 3971 (class 2606 OID 43097)
-- Name: categorization_audit categorization_audit_old_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_old_category_id_fkey FOREIGN KEY (old_category_id) REFERENCES public.categories(id);


--
-- TOC entry 3972 (class 2606 OID 43102)
-- Name: categorization_audit categorization_audit_old_chart_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_old_chart_account_id_fkey FOREIGN KEY (old_chart_account_id) REFERENCES public.chart_of_accounts(id);


--
-- TOC entry 3973 (class 2606 OID 43107)
-- Name: categorization_audit categorization_audit_old_tax_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_old_tax_category_id_fkey FOREIGN KEY (old_tax_category_id) REFERENCES public.tax_categories(id);


--
-- TOC entry 3974 (class 2606 OID 43112)
-- Name: categorization_audit categorization_audit_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id) ON DELETE CASCADE;


--
-- TOC entry 3975 (class 2606 OID 43117)
-- Name: categorization_audit categorization_audit_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_audit
    ADD CONSTRAINT categorization_audit_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3949 (class 2606 OID 42795)
-- Name: categorization_rules categorization_rules_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_rules
    ADD CONSTRAINT categorization_rules_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- TOC entry 3950 (class 2606 OID 42800)
-- Name: categorization_rules categorization_rules_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorization_rules
    ADD CONSTRAINT categorization_rules_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3964 (class 2606 OID 43049)
-- Name: category_mappings category_mappings_chart_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_chart_account_id_fkey FOREIGN KEY (chart_account_id) REFERENCES public.chart_of_accounts(id);


--
-- TOC entry 3965 (class 2606 OID 43054)
-- Name: category_mappings category_mappings_source_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_source_category_id_fkey FOREIGN KEY (source_category_id) REFERENCES public.categories(id);


--
-- TOC entry 3966 (class 2606 OID 43059)
-- Name: category_mappings category_mappings_tax_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_tax_category_id_fkey FOREIGN KEY (tax_category_id) REFERENCES public.tax_categories(id);


--
-- TOC entry 3967 (class 2606 OID 43064)
-- Name: category_mappings category_mappings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3960 (class 2606 OID 42978)
-- Name: chart_of_accounts chart_of_accounts_parent_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_of_accounts
    ADD CONSTRAINT chart_of_accounts_parent_account_id_fkey FOREIGN KEY (parent_account_id) REFERENCES public.chart_of_accounts(id);


--
-- TOC entry 3961 (class 2606 OID 42983)
-- Name: chart_of_accounts chart_of_accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_of_accounts
    ADD CONSTRAINT chart_of_accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3942 (class 2606 OID 43126)
-- Name: transactions fk_transactions_chart_account; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT fk_transactions_chart_account FOREIGN KEY (chart_account_id) REFERENCES public.chart_of_accounts(id);


--
-- TOC entry 3943 (class 2606 OID 43131)
-- Name: transactions fk_transactions_tax_category; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT fk_transactions_tax_category FOREIGN KEY (tax_category_id) REFERENCES public.tax_categories(id);


--
-- TOC entry 3978 (class 2606 OID 43207)
-- Name: journal_entries journal_entries_automation_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_automation_rule_id_fkey FOREIGN KEY (automation_rule_id) REFERENCES public.bookkeeping_rules(id) ON DELETE SET NULL;


--
-- TOC entry 3979 (class 2606 OID 43202)
-- Name: journal_entries journal_entries_period_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_period_id_fkey FOREIGN KEY (period_id) REFERENCES public.accounting_periods(id) ON DELETE SET NULL;


--
-- TOC entry 3980 (class 2606 OID 43197)
-- Name: journal_entries journal_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3981 (class 2606 OID 43230)
-- Name: journal_entry_lines journal_entry_lines_chart_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_chart_account_id_fkey FOREIGN KEY (chart_account_id) REFERENCES public.chart_of_accounts(id) ON DELETE SET NULL;


--
-- TOC entry 3982 (class 2606 OID 43225)
-- Name: journal_entry_lines journal_entry_lines_journal_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_journal_entry_id_fkey FOREIGN KEY (journal_entry_id) REFERENCES public.journal_entries(id) ON DELETE CASCADE;


--
-- TOC entry 3983 (class 2606 OID 43240)
-- Name: journal_entry_lines journal_entry_lines_tax_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_tax_category_id_fkey FOREIGN KEY (tax_category_id) REFERENCES public.tax_categories(id) ON DELETE SET NULL;


--
-- TOC entry 3984 (class 2606 OID 43235)
-- Name: journal_entry_lines journal_entry_lines_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id) ON DELETE SET NULL;


--
-- TOC entry 3947 (class 2606 OID 42766)
-- Name: ml_predictions ml_predictions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_predictions
    ADD CONSTRAINT ml_predictions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- TOC entry 3948 (class 2606 OID 42771)
-- Name: ml_predictions ml_predictions_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_predictions
    ADD CONSTRAINT ml_predictions_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- TOC entry 3936 (class 2606 OID 42638)
-- Name: plaid_items plaid_items_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plaid_items
    ADD CONSTRAINT plaid_items_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- TOC entry 3937 (class 2606 OID 42643)
-- Name: plaid_items plaid_items_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plaid_items
    ADD CONSTRAINT plaid_items_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3956 (class 2606 OID 42913)
-- Name: plaid_webhooks plaid_webhooks_original_webhook_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plaid_webhooks
    ADD CONSTRAINT plaid_webhooks_original_webhook_id_fkey FOREIGN KEY (original_webhook_id) REFERENCES public.plaid_webhooks(id);


--
-- TOC entry 3957 (class 2606 OID 42918)
-- Name: plaid_webhooks plaid_webhooks_plaid_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plaid_webhooks
    ADD CONSTRAINT plaid_webhooks_plaid_item_id_fkey FOREIGN KEY (plaid_item_id) REFERENCES public.plaid_items(id);


--
-- TOC entry 3987 (class 2606 OID 43275)
-- Name: reconciliation_items reconciliation_items_reconciliation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation_items
    ADD CONSTRAINT reconciliation_items_reconciliation_id_fkey FOREIGN KEY (reconciliation_id) REFERENCES public.reconciliation_records(id) ON DELETE CASCADE;


--
-- TOC entry 3988 (class 2606 OID 43280)
-- Name: reconciliation_items reconciliation_items_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation_items
    ADD CONSTRAINT reconciliation_items_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id) ON DELETE SET NULL;


--
-- TOC entry 3985 (class 2606 OID 43256)
-- Name: reconciliation_records reconciliation_records_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation_records
    ADD CONSTRAINT reconciliation_records_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- TOC entry 3986 (class 2606 OID 43261)
-- Name: reconciliation_records reconciliation_records_reconciled_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation_records
    ADD CONSTRAINT reconciliation_records_reconciled_by_fkey FOREIGN KEY (reconciled_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 3951 (class 2606 OID 42827)
-- Name: reports reports_parent_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_parent_report_id_fkey FOREIGN KEY (parent_report_id) REFERENCES public.reports(id);


--
-- TOC entry 3952 (class 2606 OID 42832)
-- Name: reports reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3989 (class 2606 OID 43296)
-- Name: transaction_patterns transaction_patterns_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_patterns
    ADD CONSTRAINT transaction_patterns_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3944 (class 2606 OID 42726)
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id);


--
-- TOC entry 3945 (class 2606 OID 42731)
-- Name: transactions transactions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- TOC entry 3946 (class 2606 OID 42736)
-- Name: transactions transactions_contra_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_contra_transaction_id_fkey FOREIGN KEY (contra_transaction_id) REFERENCES public.transactions(id);


--
-- TOC entry 3941 (class 2606 OID 42700)
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


-- Completed on 2025-09-19 15:28:22 PDT

--
-- PostgreSQL database dump complete
--

