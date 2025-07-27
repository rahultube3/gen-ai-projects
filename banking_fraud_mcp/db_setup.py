import duckdb
import os
import sys

def get_database_path():
    """Get database path with proper fallback logic"""
    # Check environment variable first
    env_path = os.getenv('DATABASE_PATH')
    if env_path:
        return env_path
    
    # Default paths in order of preference
    default_paths = [
        'data/bank.db',
        '/app/data/bank.db',
        'bank.db'
    ]
    
    for path in default_paths:
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except Exception as e:
                print(f"Warning: Could not create directory {dir_path}: {e}")
                continue
        return path
    
    return 'bank.db'  # Final fallback

# Get database path
db_path = get_database_path()
print(f"Setting up database at: {db_path}")

try:
    conn = duckdb.connect(db_path)
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)

# Create customer profile table
try:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS customer_profiles (
        customer_id VARCHAR PRIMARY KEY,
        name VARCHAR,
        age INTEGER,
        risk_score DOUBLE
    )
    """)
    print("✅ Created customer_profiles table")
except Exception as e:
    print(f"Error creating customer_profiles table: {e}")

# Create transaction logs
try:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        txn_id VARCHAR PRIMARY KEY,
        customer_id VARCHAR,
        amount DOUBLE,
        location VARCHAR,
        timestamp VARCHAR
    )
    """)
    print("✅ Created transactions table")
except Exception as e:
    print(f"Error creating transactions table: {e}")

# Seed customer data
# Seed customer data with diverse risk profiles
customers = [
    ('cust123', 'Alice Johnson', 45, 0.1),      # Low risk - established customer
    ('cust124', 'Rahul Patel', 32, 0.25),      # Low-medium risk - young professional
    ('cust125', 'Dinesh Kumar', 28, 0.15),     # Low risk - regular customer
    ('cust126', 'Deepti Singh', 35, 0.3),      # Medium risk - some past issues
    ('cust127', 'Aria Chen', 24, 0.45),       # Medium-high risk - young, new patterns
    ('cust128', 'Reyansh Shah', 38, 0.2),     # Low-medium risk - business owner
    ('cust129', 'Maria Garcia', 52, 0.05),    # Very low risk - long-time customer
    ('cust130', 'John Suspicious', 29, 0.75), # High risk - previous fraud attempts
    ('cust131', 'Emma Traveler', 41, 0.35),   # Medium risk - frequent international travel
    ('cust132', 'Max HighRoller', 33, 0.8),   # Very high risk - gambling history
]

for customer in customers:
    try:
        conn.execute("INSERT OR REPLACE INTO customer_profiles VALUES (?, ?, ?, ?)", customer)
    except Exception as e:
        print(f"Error inserting customer {customer[0]}: {e}")

print(f"✅ Inserted {len(customers)} customer profiles")

# Seed transaction data with diverse risk profiles
transactions = [
    # MINIMAL RISK - Very safe transactions
    ('txn001', 'cust129', 15.0, 'HomeCity', '2025-07-24T14:30:00'),       # Coffee purchase
    ('txn002', 'cust129', 8.50, 'HomeCity', '2025-07-24T16:45:00'),       # Lunch
    ('txn003', 'cust129', 25.0, 'HomeCity', '2025-07-24T12:15:00'),       # Grocery store
    ('txn004', 'cust129', 45.0, 'HomeCity', '2025-07-24T18:20:00'),       # Pharmacy
    ('txn005', 'cust129', 12.75, 'HomeCity', '2025-07-24T08:30:00'),      # Parking
    ('txn006', 'cust129', 35.0, 'HomeCity', '2025-07-24T19:15:00'),       # Dinner
    ('txn007', 'cust129', 22.50, 'HomeCity', '2025-07-24T13:45:00'),      # Book store
    ('txn008', 'cust129', 18.0, 'HomeCity', '2025-07-24T11:30:00'),       # Movie ticket
    
    # LOW RISK - Normal transactions
    ('txn010', 'cust123', 150.0, 'HomeCity', '2025-07-24T14:30:00'),      # Small amount, safe location
    ('txn011', 'cust123', 85.0, 'HomeCity', '2025-07-24T16:45:00'),       # Small amount, safe location
    ('txn012', 'cust124', 250.0, 'HomeCity', '2025-07-24T12:15:00'),      # Small amount, safe location
    ('txn013', 'cust125', 320.0, 'ShoppingMall', '2025-07-24T18:20:00'),  # Normal shopping
    ('txn014', 'cust126', 75.0, 'GasStation', '2025-07-24T08:30:00'),     # Gas purchase
    ('txn015', 'cust129', 450.0, 'HomeCity', '2025-07-24T15:00:00'),      # Grocery shopping
    ('txn016', 'cust123', 275.0, 'HomeCity', '2025-07-24T17:30:00'),      # Department store
    ('txn017', 'cust124', 125.0, 'HomeCity', '2025-07-24T20:00:00'),      # Restaurant
    
    # MEDIUM RISK - Somewhat suspicious transactions
    ('txn020', 'cust127', 2500.0, 'HomeCity', '2025-07-24T22:15:00'),     # High amount, late hour
    ('txn021', 'cust124', 1800.0, 'NewYork', '2025-07-24T11:00:00'),      # Moderate amount, unfamiliar location
    ('txn022', 'cust125', 3200.0, 'Atlanta', '2025-07-24T13:45:00'),      # High amount, travel location
    ('txn023', 'cust126', 1500.0, 'Miami', '2025-07-24T19:30:00'),        # Moderate amount, vacation spot
    ('txn024', 'cust127', 2800.0, 'HomeCity', '2025-07-25T02:30:00'),     # High amount, very late hour
    ('txn025', 'cust131', 3500.0, 'Chicago', '2025-07-24T21:45:00'),      # Travel transaction
    ('txn026', 'cust128', 2200.0, 'Boston', '2025-07-24T23:15:00'),       # Late night, travel
    
    # HIGH RISK - Very suspicious transactions  
    ('txn030', 'cust130', 8500.0, 'LasVegas', '2025-07-24T23:45:00'),     # High amount, risky location, late
    ('txn031', 'cust130', 12000.0, 'Unknown', '2025-07-25T03:20:00'),     # Very high amount, unknown location, night
    ('txn032', 'cust132', 15000.0, 'International', '2025-07-24T01:15:00'), # Very high, international, night
    ('txn033', 'cust132', 25000.0, 'LasVegas', '2025-07-25T04:30:00'),    # Extremely high, casino, dawn
    ('txn034', 'cust130', 18000.0, 'DarkWeb', '2025-07-24T02:45:00'),     # High amount, suspicious location
    ('txn035', 'cust132', 22000.0, 'Offshore', '2025-07-25T03:45:00'),    # High amount, offshore, night
    ('txn036', 'cust130', 16500.0, 'BitcoinATM', '2025-07-24T01:20:00'),  # Crypto purchase, night
    ('txn037', 'cust132', 28000.0, 'MoneyLaundering', '2025-07-25T02:15:00'), # Suspicious merchant
    ('txn038', 'cust130', 19000.0, 'CasinoChip', '2025-07-24T03:30:00'),  # Casino, very late
    
    # CRITICAL RISK - Extremely suspicious patterns
    ('txn040', 'cust132', 50000.0, 'Unknown', '2025-07-25T03:00:00'),     # Extremely high, unknown, night
    ('txn041', 'cust130', 75000.0, 'International', '2025-07-25T02:15:00'), # Extremely high, international
    ('txn042', 'cust132', 45000.0, 'LasVegas', '2025-07-24T04:20:00'),    # Extremely high, casino, dawn
    ('txn043', 'cust130', 100000.0, 'Offshore', '2025-07-25T01:30:00'),   # Massive amount, offshore
    ('txn044', 'cust132', 85000.0, 'Cryptocurrency', '2025-07-25T03:15:00'), # Massive crypto
    ('txn045', 'cust130', 120000.0, 'ShellCompany', '2025-07-24T02:00:00'), # Shell company transfer
    
    # RAPID FIRE PATTERNS - Multiple transactions (velocity risk)
    ('txn050', 'cust130', 3000.0, 'NewYork', '2025-07-24T14:00:00'),      # Start of rapid sequence
    ('txn051', 'cust130', 2800.0, 'NewYork', '2025-07-24T14:05:00'),      # 5 minutes later
    ('txn052', 'cust130', 3200.0, 'NewYork', '2025-07-24T14:12:00'),      # 7 minutes later
    ('txn053', 'cust130', 2900.0, 'NewYork', '2025-07-24T14:18:00'),      # 6 minutes later
    ('txn054', 'cust130', 3100.0, 'NewYork', '2025-07-24T14:25:00'),      # 7 minutes later
    
    # LOCATION HOPPING - Impossible travel patterns
    ('txn060', 'cust132', 1500.0, 'NewYork', '2025-07-24T10:00:00'),      # Start in NY
    ('txn061', 'cust132', 1200.0, 'LosAngeles', '2025-07-24T10:30:00'),   # 30 mins later in LA (impossible)
    ('txn062', 'cust132', 1800.0, 'Miami', '2025-07-24T11:00:00'),        # 30 mins later in Miami (impossible)
    ('txn063', 'cust132', 2200.0, 'London', '2025-07-24T11:15:00'),       # 15 mins later in London (impossible)
    
    # UNUSUAL MERCHANT TYPES (HIGH RISK)
    ('txn070', 'cust130', 5000.0, 'CryptoCurrency', '2025-07-24T20:15:00'), # Crypto purchase
    ('txn071', 'cust132', 8000.0, 'GoldDealer', '2025-07-24T21:30:00'),     # Gold purchase
    ('txn072', 'cust130', 12000.0, 'MoneyTransfer', '2025-07-24T22:45:00'), # Money transfer
    ('txn073', 'cust132', 9500.0, 'PawnShop', '2025-07-24T23:20:00'),       # Pawn shop, late
    ('txn074', 'cust130', 7500.0, 'CheckCashing', '2025-07-25T01:40:00'),   # Check cashing, night
    
    # WEEKEND AND HOLIDAY SUSPICIOUS PATTERNS
    ('txn080', 'cust130', 15000.0, 'LasVegas', '2025-07-26T02:30:00'),     # Weekend, casino, night
    ('txn081', 'cust132', 22000.0, 'International', '2025-07-27T03:45:00'), # Sunday night, international
    ('txn082', 'cust130', 18500.0, 'Unknown', '2025-07-26T04:15:00'),      # Weekend dawn transaction
]

for transaction in transactions:
    try:
        conn.execute("INSERT OR REPLACE INTO transactions VALUES (?, ?, ?, ?, ?)", transaction)
    except Exception as e:
        print(f"Error inserting transaction {transaction[0]}: {e}")

print(f"✅ Inserted {len(transactions)} transactions")

# Verify data
try:
    customer_count = conn.execute("SELECT COUNT(*) FROM customer_profiles").fetchone()[0]
    transaction_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    print(f"✅ Database verification: {customer_count} customers, {transaction_count} transactions")
except Exception as e:
    print(f"Error verifying data: {e}")

try:
    conn.close()
    print(f"✅ Database setup completed successfully at: {db_path}")
except Exception as e:
    print(f"Error closing connection: {e}")
