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

