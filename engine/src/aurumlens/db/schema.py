"""DuckDB Schema Definitions for AurumLens local analytics storage.

Mirrors the Supabase schema from ANTIGRAVITY_BUILD_PLAN §5.1 / Design §5.
"""

DDL_SOURCE_FILE = """
CREATE SEQUENCE IF NOT EXISTS seq_source_file_id START 1;

CREATE TABLE IF NOT EXISTS source_file (
    file_id BIGINT PRIMARY KEY DEFAULT nextval('seq_source_file_id'),
    requested_date DATE NOT NULL,
    returned_date DATE,
    adapter VARCHAR NOT NULL,
    sha256 VARCHAR NOT NULL UNIQUE,
    storage_path VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    reject_reason VARCHAR,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_CONTRACT_SPEC = """
CREATE TABLE IF NOT EXISTS contract_spec (
    symbol VARCHAR PRIMARY KEY,
    trading_unit_g DOUBLE,
    quote_basis_g DOUBLE,
    purity DOUBLE,
    expiry_rule VARCHAR,
    tender_days INTEGER,
    tick_size DOUBLE,
    field_status VARCHAR NOT NULL DEFAULT '{}',
    source_reference VARCHAR,
    verified_at TIMESTAMP
);
"""

DDL_CONTRACT = """
CREATE TABLE IF NOT EXISTS contract (
    contract_id VARCHAR PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    expiry_date DATE NOT NULL,
    first_seen DATE,
    last_seen DATE,
    UNIQUE (symbol, expiry_date)
);
"""

DDL_DAILY_PRICE = """
CREATE TABLE IF NOT EXISTS daily_price (
    contract_id VARCHAR NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    settlement DOUBLE,
    volume BIGINT,
    open_interest BIGINT,
    price_used DOUBLE,
    price_source VARCHAR,
    price_quality VARCHAR NOT NULL,
    quality_reason VARCHAR,
    normalized_price DOUBLE,
    file_id BIGINT NOT NULL,
    dataset_version VARCHAR NOT NULL,
    PRIMARY KEY (contract_id, trade_date)
);
"""

ALL_DDL = [
    DDL_SOURCE_FILE,
    DDL_CONTRACT_SPEC,
    DDL_CONTRACT,
    DDL_DAILY_PRICE
]
