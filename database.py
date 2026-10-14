import sqlite3
from datetime import datetime

DB_NAME = "settlement_engine.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name like a dictionary
    return conn

def init_db():
    """Initializes the multi-currency liquidity database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Table for Central Bank Reserve Pools
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS central_bank_reserves (
            currency_code TEXT PRIMARY KEY,    -- e.g., NGN, GHS, KES, ZAR, EGP
            bank_name TEXT NOT NULL,           -- e.g., Central Bank of Nigeria
            available_liquidity REAL NOT NULL, -- Current pre-funded balance
            min_alert_threshold REAL NOT NULL, -- Trigger alert if balance drops below this
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Table for Real-Time FX Exchange Rates (Matrix Representation)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fx_rates (
            source_currency TEXT,
            target_currency TEXT,
            rate REAL NOT NULL,                -- Base rate multiplier
            liquidity_fee_percentage REAL DEFAULT 0.01, -- Fee for using this corridor
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source_currency, target_currency)
        )
    ''')
    
    # 3. Table for Transaction Tracking & Auditing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settlement_transactions (
            transaction_id TEXT PRIMARY KEY,
            source_currency TEXT NOT NULL,
            target_currency TEXT NOT NULL,
            amount REAL NOT NULL,
            settled_amount REAL,
            routing_path TEXT,                 -- e.g., "NGN -> ZAR -> GHS"
            status TEXT NOT NULL,              -- SETTLED, FAILED_LIQUIDITY, PENDING
            failure_reason TEXT,               -- Explains where the shortfall occurred
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Seed with initial mock regional data if empty
    cursor.execute("SELECT COUNT(*) FROM central_bank_reserves")
    if cursor.fetchone()[0] == 0:
        mock_reserves = [
            ('NGN', 'Central Bank of Nigeria', 50000000.0, 5000000.0),
            ('GHS', 'Bank of Ghana', 120000.0, 20000.0),         # Purposefully low for stress-testing
            ('KES', 'Central Bank of Kenya', 15000000.0, 1500000.0),
            ('ZAR', 'South African Reserve Bank', 45000000.0, 4000000.0),
            ('EGP', 'Central Bank of Egypt', 30000000.0, 3000000.0)
        ]
        cursor.executemany('''
            INSERT INTO central_bank_reserves (currency_code, bank_name, available_liquidity, min_alert_threshold)
            VALUES (?, ?, ?, ?)
        ''', mock_reserves)
        
    conn.commit()
    conn.close()
    print("✅ Database initialized with PAPSS-inspired core tables.")

if __name__ == "__main__":
    init_db()
