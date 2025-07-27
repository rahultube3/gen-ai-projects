import duckdb

conn = duckdb.connect("banking_fraud_mcp/bank.db")

# Create customer profile table
conn.execute("""
CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    age INTEGER,
    risk_score DOUBLE
)
""")

# Create transaction logs
conn.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    txn_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR,
    amount DOUBLE,
    location VARCHAR,
    timestamp VARCHAR
)
""")

# Seed data
conn.execute("INSERT OR REPLACE INTO customer_profiles VALUES ('cust123', 'Alice', 45, 0.1)")
conn.execute("INSERT OR REPLACE INTO customer_profiles VALUES ('cust124', 'Rahul', 45, 0.3)")
conn.execute("INSERT OR REPLACE INTO customer_profiles VALUES ('cust125', 'Dinesh', 45, 0.2)")
conn.execute("INSERT OR REPLACE INTO transactions VALUES ('txn001', 'cust123', 4000.0, 'New York', '2025-07-24T10:00:00')")
conn.execute("INSERT OR REPLACE INTO transactions VALUES ('txn002', 'cust123', 4000.0, 'New York', '2025-07-24T10:00:00')")
conn.execute("INSERT OR REPLACE INTO transactions VALUES ('txn021', 'cust124', 4000.0, 'New York', '2025-07-24T10:00:00')")
conn.execute("INSERT OR REPLACE INTO transactions VALUES ('txn022', 'cust124', 4000.0, 'New York', '2025-07-24T10:00:00')")
conn.execute("INSERT OR REPLACE INTO transactions VALUES ('txn031', 'cust125', 4000.0, 'New York', '2025-07-24T10:00:00')")
conn.execute("INSERT OR REPLACE INTO transactions VALUES ('txn032', 'cust125', 4000.0, 'New York', '2025-07-24T10:00:00')")

conn.close()
