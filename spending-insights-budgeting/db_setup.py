import duckdb
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import json
import random
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Transaction:
    """Transaction data class for type safety"""
    date: str
    merchant: str
    category: str
    amount: float
    notes: str

@dataclass
class BudgetCategory:
    """Budget category data class"""
    category: str
    monthly_limit: float
    alert_threshold: float

@dataclass
class FinancialGoal:
    """Financial goal data class"""
    goal_name: str
    target_amount: float
    current_amount: float
    target_date: str
    priority: str

class SpendingDataGenerator:
    """Generate realistic spending data for testing"""
    
    MERCHANTS = {
        "Dining": ["Starbucks", "Chipotle", "McDonald's", "Subway", "Pizza Hut", "Taco Bell", "Domino's"],
        "Groceries": ["Whole Foods", "Costco", "Safeway", "Trader Joe's", "Kroger", "Target"],
        "Shopping": ["Amazon", "Target", "Walmart", "Best Buy", "Macy's", "Nike"],
        "Transport": ["Uber", "Lyft", "Shell", "Chevron", "Metro", "BART"],
        "Entertainment": ["Netflix", "Spotify", "Apple Music", "Hulu", "Disney+", "HBO Max"],
        "Healthcare": ["CVS Pharmacy", "Walgreens", "Kaiser", "Urgent Care", "Dentist"],
        "Fitness": ["Gym Plus", "Planet Fitness", "24 Hour Fitness", "Yoga Studio"],
        "Home Improvement": ["Home Depot", "Lowe's", "IKEA", "Ace Hardware"],
        "Electronics": ["Best Buy", "Apple Store", "Amazon", "Newegg", "Micro Center"]
    }
    
    AMOUNT_RANGES = {
        "Dining": (5, 50),
        "Groceries": (30, 200),
        "Shopping": (20, 300),
        "Transport": (10, 80),
        "Entertainment": (5, 20),
        "Healthcare": (15, 150),
        "Fitness": (25, 100),
        "Home Improvement": (50, 500),
        "Electronics": (50, 800)
    }

    @classmethod
    def generate_transactions(cls, months: int = 6, transactions_per_month: int = 50) -> List[Transaction]:
        """Generate realistic transaction data"""
        transactions = []
        start_date = datetime.now() - timedelta(days=30 * months)
        
        for month_offset in range(months):
            month_start = start_date + timedelta(days=30 * month_offset)
            
            # Generate regular monthly subscriptions
            for day in [1, 15]:  # Subscription dates
                subscription_date = month_start + timedelta(days=day)
                if random.random() < 0.9:  # 90% chance of subscription
                    transactions.append(Transaction(
                        date=subscription_date.strftime("%Y-%m-%d"),
                        merchant=random.choice(cls.MERCHANTS["Entertainment"]),
                        category="Entertainment",
                        amount=round(random.uniform(9.99, 19.99), 2),
                        notes="Monthly subscription"
                    ))
            
            # Generate regular transactions
            for _ in range(transactions_per_month):
                category = random.choices(
                    list(cls.MERCHANTS.keys()),
                    weights=[20, 15, 12, 10, 8, 5, 5, 3, 2],  # Realistic frequency weights
                    k=1
                )[0]
                
                merchant = random.choice(cls.MERCHANTS[category])
                min_amount, max_amount = cls.AMOUNT_RANGES[category]
                amount = round(random.uniform(min_amount, max_amount), 2)
                
                # Add some variance to dates
                transaction_date = month_start + timedelta(days=random.randint(0, 29))
                
                transactions.append(Transaction(
                    date=transaction_date.strftime("%Y-%m-%d"),
                    merchant=merchant,
                    category=category,
                    amount=amount,
                    notes=cls._generate_note(category, merchant)
                ))
        
        return sorted(transactions, key=lambda t: t.date)
    
    @classmethod
    def _generate_note(cls, category: str, merchant: str) -> str:
        """Generate realistic transaction notes"""
        notes_map = {
            "Dining": ["Quick lunch", "Coffee break", "Dinner out", "Breakfast", "Team lunch"],
            "Groceries": ["Weekly shopping", "Quick pickup", "Bulk shopping", "Organic produce"],
            "Shopping": ["Online order", "In-store purchase", "Gift", "Essentials"],
            "Transport": ["Commute", "Airport trip", "Weekend ride", "Gas fill-up"],
            "Entertainment": ["Monthly subscription", "Premium upgrade", "Family plan"],
            "Healthcare": ["Prescription", "Check-up", "Emergency visit", "Vitamins"],
            "Fitness": ["Monthly membership", "Personal training", "Equipment"],
            "Home Improvement": ["Home project", "Repairs", "Gardening", "Tools"],
            "Electronics": ["Upgrade", "Replacement", "Accessories", "Work equipment"]
        }
        return random.choice(notes_map.get(category, ["General purchase"]))

class OptimizedSpendingDatabaseSetup:
    """Optimized database setup with DuckDB compatibility"""
    
    def __init__(self, db_path: str = "spending_insights.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self.backup_path = self.db_path.with_suffix('.backup.db')

    def connect(self) -> None:
        """Connect to DuckDB with optimized settings"""
        try:
            # Create backup if database exists
            if self.db_path.exists():
                self._create_backup()
            
            self.conn = duckdb.connect(str(self.db_path))
            
            # Optimize DuckDB settings (corrected for DuckDB)
            self.conn.execute("SET memory_limit='1GB'")
            self.conn.execute("SET threads TO 4")
            self.conn.execute("SET enable_progress_bar=true")
            
            print(f"✅ Connected to optimized database: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            raise

    def _create_backup(self) -> None:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            print(f"📋 Backup created: {self.backup_path}")
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")

    def create_tables(self) -> None:
        """Create DuckDB-compatible database schema"""
        if not self.conn:
            raise ValueError("Database connection not established")

        try:
            # Drop existing tables in correct order
            tables_to_drop = [
                "monthly_spending_summary", 
                "spending_patterns", 
                "transactions", 
                "budget_categories", 
                "financial_goals"
            ]
            
            for table in tables_to_drop:
                self.conn.execute(f"DROP TABLE IF EXISTS {table}")
            
            # Create budget_categories table first
            self.conn.execute("""
                CREATE TABLE budget_categories (
                    id INTEGER PRIMARY KEY,
                    category VARCHAR UNIQUE NOT NULL,
                    monthly_limit DECIMAL(10,2) NOT NULL,
                    alert_threshold DECIMAL(3,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create transactions table (removed foreign key constraint for compatibility)
            self.conn.execute("""
                CREATE TABLE transactions (
                    id INTEGER PRIMARY KEY,
                    date DATE NOT NULL,
                    merchant VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX idx_transactions_date ON transactions(date)",
                "CREATE INDEX idx_transactions_category ON transactions(category)",
                "CREATE INDEX idx_transactions_merchant ON transactions(merchant)",
                "CREATE INDEX idx_transactions_amount ON transactions(amount)",
                "CREATE INDEX idx_transactions_date_category ON transactions(date, category)"
            ]
            
            for index in indexes:
                self.conn.execute(index)

            # Financial goals table
            self.conn.execute("""
                CREATE TABLE financial_goals (
                    id INTEGER PRIMARY KEY,
                    goal_name VARCHAR NOT NULL UNIQUE,
                    target_amount DECIMAL(10,2) NOT NULL,
                    current_amount DECIMAL(10,2) DEFAULT 0.00,
                    target_date DATE,
                    priority VARCHAR,
                    status VARCHAR DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Monthly summary table
            self.conn.execute("""
                CREATE TABLE monthly_spending_summary (
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    category VARCHAR NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    transaction_count INTEGER NOT NULL,
                    average_amount DECIMAL(10,2) NOT NULL,
                    median_amount DECIMAL(10,2),
                    max_amount DECIMAL(10,2),
                    min_amount DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(year, month, category)
                )
            """)

            # Spending patterns table
            self.conn.execute("""
                CREATE TABLE spending_patterns (
                    id INTEGER PRIMARY KEY,
                    pattern_type VARCHAR NOT NULL,
                    pattern_description TEXT NOT NULL,
                    category VARCHAR,
                    merchant VARCHAR,
                    frequency VARCHAR,
                    avg_amount DECIMAL(10,2),
                    median_amount DECIMAL(10,2),
                    confidence_score DECIMAL(3,2),
                    sample_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create analytics view
            self.conn.execute("""
                CREATE VIEW transaction_analytics AS
                SELECT 
                    category,
                    COUNT(*) as total_transactions,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    MEDIAN(amount) as median_amount,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount,
                    STDDEV(amount) as stddev_amount,
                    COUNT(DISTINCT merchant) as unique_merchants,
                    MIN(date) as first_transaction,
                    MAX(date) as last_transaction
                FROM transactions
                GROUP BY category
            """)

            print("✅ DuckDB-compatible database schema created successfully")
            print("✅ Indexes created for performance")
            print("✅ Analytics view created")

        except Exception as e:
            print(f"❌ Error creating schema: {e}")
            raise

    def insert_sample_data(self, generate_large_dataset: bool = True) -> None:
        """Insert optimized sample data with batch operations"""
        if not self.conn:
            raise ValueError("Database connection not established")

        try:
            # Start transaction for better performance
            self.conn.execute("BEGIN TRANSACTION")
            
            # Clear existing data
            for table in ["monthly_spending_summary", "spending_patterns", "transactions", "financial_goals", "budget_categories"]:
                self.conn.execute(f"DELETE FROM {table}")

            # Insert budget categories first
            budget_categories = [
                BudgetCategory("Dining", 300.00, 0.8),
                BudgetCategory("Groceries", 500.00, 0.75),
                BudgetCategory("Shopping", 400.00, 0.85),
                BudgetCategory("Transport", 200.00, 0.9),
                BudgetCategory("Entertainment", 80.00, 0.8),
                BudgetCategory("Healthcare", 150.00, 0.7),
                BudgetCategory("Fitness", 120.00, 0.9),
                BudgetCategory("Home Improvement", 600.00, 0.8),
                BudgetCategory("Electronics", 500.00, 0.75)
            ]

            # Batch insert budget categories
            budget_data = [
                (idx, budget.category, budget.monthly_limit, budget.alert_threshold)
                for idx, budget in enumerate(budget_categories, 1)
            ]
            
            self.conn.executemany("""
                INSERT INTO budget_categories (id, category, monthly_limit, alert_threshold)
                VALUES (?, ?, ?, ?)
            """, budget_data)

            # Generate and insert transactions
            if generate_large_dataset:
                transactions = SpendingDataGenerator.generate_transactions(months=12, transactions_per_month=80)
            else:
                transactions = self._get_basic_transactions()

            # Batch insert transactions with validation
            transaction_data = []
            valid_categories = [b.category for b in budget_categories]
            
            for idx, transaction in enumerate(transactions, 1):
                # Validate category exists in budget_categories
                if transaction.category not in valid_categories:
                    transaction.category = "Shopping"  # Default fallback
                
                transaction_data.append((
                    idx,
                    transaction.date,
                    transaction.merchant,
                    transaction.category,
                    transaction.amount,
                    transaction.notes
                ))

            self.conn.executemany("""
                INSERT INTO transactions (id, date, merchant, category, amount, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, transaction_data)

            # Insert financial goals
            financial_goals = [
                FinancialGoal("Emergency Fund", 15000.00, 4500.00, "2024-12-31", "High"),
                FinancialGoal("Vacation Fund", 3500.00, 1200.00, "2024-11-15", "Medium"),
                FinancialGoal("New Car Fund", 8000.00, 2100.00, "2025-06-01", "Medium"),
                FinancialGoal("Home Down Payment", 50000.00, 12000.00, "2025-12-31", "High"),
                FinancialGoal("Tech Upgrade Fund", 2000.00, 500.00, "2024-12-15", "Low")
            ]

            goal_data = [
                (idx, goal.goal_name, goal.target_amount, goal.current_amount, goal.target_date, goal.priority)
                for idx, goal in enumerate(financial_goals, 1)
            ]

            self.conn.executemany("""
                INSERT INTO financial_goals (id, goal_name, target_amount, current_amount, target_date, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, goal_data)

            # Commit transaction
            self.conn.execute("COMMIT")

            print(f"✅ Inserted {len(transaction_data)} transactions (batch operation)")
            print(f"✅ Inserted {len(budget_categories)} budget categories")
            print(f"✅ Inserted {len(financial_goals)} financial goals")

        except Exception as e:
            self.conn.execute("ROLLBACK")
            print(f"❌ Error inserting sample data: {e}")
            raise

    def _get_basic_transactions(self) -> List[Transaction]:
        """Get basic transaction set for testing"""
        return [
            Transaction("2024-07-01", "Starbucks", "Dining", 5.75, "Morning coffee"),
            Transaction("2024-07-03", "Whole Foods", "Groceries", 72.12, "Weekly groceries"),
            Transaction("2024-07-15", "Amazon", "Shopping", 120.50, "New headphones"),
            Transaction("2024-07-20", "Uber", "Transport", 18.30, "Ride to airport"),
            Transaction("2024-07-25", "Chipotle", "Dining", 12.50, "Lunch"),
            Transaction("2024-08-02", "Costco", "Groceries", 156.78, "Bulk shopping"),
            Transaction("2024-08-05", "Starbucks", "Dining", 6.25, "Iced coffee"),
            Transaction("2024-08-10", "Home Depot", "Home Improvement", 234.56, "Garden supplies"),
        ]

    def generate_optimized_analytics(self) -> None:
        """Generate comprehensive analytics with statistical measures"""
        if not self.conn:
            raise ValueError("Database connection not established")

        try:
            print("📊 Generating optimized analytics...")
            
            # Generate enhanced monthly summaries
            self.conn.execute("DELETE FROM monthly_spending_summary")
            
            self.conn.execute("""
                INSERT INTO monthly_spending_summary (
                    year, month, category, total_amount, transaction_count, 
                    average_amount, median_amount, max_amount, min_amount
                )
                SELECT 
                    EXTRACT(YEAR FROM date) as year,
                    EXTRACT(MONTH FROM date) as month,
                    category,
                    SUM(amount) as total_amount,
                    COUNT(*) as transaction_count,
                    AVG(amount) as average_amount,
                    MEDIAN(amount) as median_amount,
                    MAX(amount) as max_amount,
                    MIN(amount) as min_amount
                FROM transactions
                GROUP BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date), category
                HAVING COUNT(*) >= 2
                ORDER BY year, month, category
            """)

            # Generate intelligent spending patterns
            self.conn.execute("DELETE FROM spending_patterns")
            
            # Detect high-frequency merchants
            high_frequency_patterns = self.conn.execute("""
                SELECT 
                    'High Frequency Merchant' as pattern_type,
                    'Regular purchases at ' || merchant || ' (' || category || ')' as pattern_description,
                    category,
                    merchant,
                    CASE 
                        WHEN COUNT(*) >= 20 THEN 'Very Frequent'
                        WHEN COUNT(*) >= 10 THEN 'Frequent'
                        ELSE 'Regular'
                    END as frequency,
                    AVG(amount) as avg_amount,
                    MEDIAN(amount) as median_amount,
                    CASE 
                        WHEN COUNT(*) >= 20 THEN 0.95
                        WHEN COUNT(*) >= 10 THEN 0.85
                        ELSE 0.75
                    END as confidence_score,
                    COUNT(*) as sample_size
                FROM transactions
                GROUP BY merchant, category
                HAVING COUNT(*) >= 5
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """).fetchall()

            # Insert high-frequency patterns
            for idx, pattern in enumerate(high_frequency_patterns, 1):
                self.conn.execute("""
                    INSERT INTO spending_patterns (
                        id, pattern_type, pattern_description, category, merchant,
                        frequency, avg_amount, median_amount, confidence_score, sample_size
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [idx] + list(pattern))

            # Detect subscription patterns
            subscription_patterns = self.conn.execute("""
                SELECT DISTINCT
                    'Subscription Pattern' as pattern_type,
                    'Monthly subscription to ' || merchant as pattern_description,
                    category,
                    merchant,
                    'Monthly' as frequency,
                    AVG(amount) as avg_amount,
                    MEDIAN(amount) as median_amount,
                    0.90 as confidence_score,
                    COUNT(*) as sample_size
                FROM transactions
                WHERE amount BETWEEN 5 AND 50
                    AND (notes LIKE '%subscription%' OR notes LIKE '%monthly%')
                GROUP BY merchant, category
                HAVING COUNT(*) >= 2
            """).fetchall()

            # Insert subscription patterns
            pattern_id = len(high_frequency_patterns) + 1
            for pattern in subscription_patterns:
                self.conn.execute("""
                    INSERT INTO spending_patterns (
                        id, pattern_type, pattern_description, category, merchant,
                        frequency, avg_amount, median_amount, confidence_score, sample_size
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [pattern_id] + list(pattern))
                pattern_id += 1

            # Get counts for reporting
            summary_count = self.conn.execute("SELECT COUNT(*) FROM monthly_spending_summary").fetchone()[0]
            patterns_count = self.conn.execute("SELECT COUNT(*) FROM spending_patterns").fetchone()[0]
            
            print(f"✅ Generated {summary_count} enhanced monthly summaries")
            print(f"✅ Generated {patterns_count} intelligent spending patterns")

        except Exception as e:
            print(f"❌ Error generating analytics: {e}")
            raise

    def optimize_database(self) -> None:
        """Run database optimization operations"""
        if not self.conn:
            raise ValueError("Database connection not established")

        try:
            print("🔧 Optimizing database performance...")
            
            # Analyze tables for better query planning (DuckDB compatible)
            tables = ["transactions", "budget_categories", "financial_goals", "monthly_spending_summary", "spending_patterns"]
            for table in tables:
                try:
                    self.conn.execute(f"ANALYZE {table}")
                except Exception:
                    # Skip if ANALYZE not supported in this DuckDB version
                    pass
            
            print("✅ Database optimization completed")

        except Exception as e:
            print(f"❌ Error optimizing database: {e}")
            raise

    def display_enhanced_stats(self) -> None:
        """Display comprehensive database statistics"""
        if not self.conn:
            raise ValueError("Database connection not established")

        try:
            print("\n" + "="*60)
            print("📊 ENHANCED DATABASE STATISTICS")
            print("="*60)

            # Get database file size
            db_size = self.db_path.stat().st_size / (1024 * 1024)  # MB
            print(f"💾 Database Size: {db_size:.2f} MB")

            # Transaction statistics with performance metrics
            start_time = datetime.now()
            stats = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_transactions,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    MEDIAN(amount) as median_amount,
                    STDDEV(amount) as stddev_amount,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(DISTINCT category) as unique_categories,
                    COUNT(DISTINCT merchant) as unique_merchants
                FROM transactions
            """).fetchone()
            query_time = (datetime.now() - start_time).total_seconds()

            print(f"💳 TRANSACTION ANALYSIS (Query time: {query_time:.3f}s):")
            print(f"   • Total Transactions: {stats[0]:,}")
            print(f"   • Total Amount: ${stats[1]:,.2f}")
            print(f"   • Average Transaction: ${stats[2]:.2f}")
            print(f"   • Median Transaction: ${stats[3]:.2f}")
            print(f"   • Standard Deviation: ${stats[4]:.2f}")
            print(f"   • Date Range: {stats[5]} to {stats[6]}")
            print(f"   • Unique Categories: {stats[7]}")
            print(f"   • Unique Merchants: {stats[8]}")

            # Category analysis with rankings
            print(f"\n📈 TOP SPENDING CATEGORIES:")
            category_stats = self.conn.execute("""
                SELECT 
                    category, 
                    COUNT(*) as transactions,
                    SUM(amount) as total,
                    AVG(amount) as avg_amount,
                    MEDIAN(amount) as median_amount,
                    (SUM(amount) * 100.0 / (SELECT SUM(amount) FROM transactions)) as percentage
                FROM transactions 
                GROUP BY category 
                ORDER BY total DESC
                LIMIT 10
            """).fetchall()

            for i, (category, count, total, avg, median, pct) in enumerate(category_stats, 1):
                print(f"   {i:2d}. {category:<20} | {count:3d} txns | ${total:8.2f} | ${avg:6.2f} avg | ${median:6.2f} med | {pct:5.1f}%")

            # Budget health analysis
            print(f"\n💰 BUDGET HEALTH ANALYSIS:")
            budget_health = self.conn.execute("""
                SELECT 
                    bc.category,
                    bc.monthly_limit,
                    COALESCE(current_month.monthly_spent, 0) as current_spent,
                    (COALESCE(current_month.monthly_spent, 0) / bc.monthly_limit * 100) as usage_pct
                FROM budget_categories bc
                LEFT JOIN (
                    SELECT 
                        category,
                        SUM(amount) as monthly_spent
                    FROM transactions
                    WHERE EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                        AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                    GROUP BY category
                ) current_month ON bc.category = current_month.category
                ORDER BY usage_pct DESC
            """).fetchall()

            healthy = warning = over_budget = 0
            for category, limit, spent, usage_pct in budget_health:
                if usage_pct >= 100:
                    status = "🚨 OVER"
                    over_budget += 1
                elif usage_pct >= 80:
                    status = "⚠️  WARN"
                    warning += 1
                else:
                    status = "✅ OK  "
                    healthy += 1
                
                print(f"   {status} {category:<20} | ${spent:7.2f} / ${limit:7.2f} | {usage_pct:5.1f}%")

            print(f"\n🎯 BUDGET SUMMARY: {healthy} Healthy | {warning} Warning | {over_budget} Over Budget")

            # Performance metrics
            table_counts = {}
            for table in ["transactions", "budget_categories", "financial_goals", "monthly_spending_summary", "spending_patterns"]:
                count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                table_counts[table] = count

            print(f"\n📋 TABLE STATISTICS:")
            for table, count in table_counts.items():
                print(f"   • {table:<25}: {count:,} records")

            print(f"\n✅ Enhanced database analysis completed!")

        except Exception as e:
            print(f"❌ Error displaying enhanced stats: {e}")
            raise

    def create_performance_report(self) -> Dict[str, Any]:
        """Generate performance report for monitoring"""
        if not self.conn:
            raise ValueError("Database connection not established")

        try:
            # Query performance test
            queries = [
                ("Simple SELECT", "SELECT COUNT(*) FROM transactions"),
                ("JOIN Query", "SELECT t.*, bc.monthly_limit FROM transactions t JOIN budget_categories bc ON t.category = bc.category LIMIT 100"),
                ("Aggregation", "SELECT category, SUM(amount), AVG(amount) FROM transactions GROUP BY category"),
                ("Date Range", "SELECT * FROM transactions WHERE date >= '2024-07-01' ORDER BY date DESC LIMIT 50")
            ]

            performance_data = {}
            for query_name, query in queries:
                start_time = datetime.now()
                result = self.conn.execute(query).fetchall()
                end_time = datetime.now()
                
                performance_data[query_name] = {
                    "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
                    "rows_returned": len(result)
                }

            # Database health metrics
            db_size = self.db_path.stat().st_size
            total_records = sum(
                self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ["transactions", "budget_categories", "financial_goals", "monthly_spending_summary", "spending_patterns"]
            )

            return {
                "timestamp": datetime.now().isoformat(),
                "database_size_bytes": db_size,
                "total_records": total_records,
                "query_performance": performance_data,
                "optimization_status": "optimized"
            }

        except Exception as e:
            print(f"❌ Error creating performance report: {e}")
            return {"error": str(e)}

    def close(self) -> None:
        """Close database connection with cleanup"""
        if self.conn:
            try:
                self.conn.close()
                print("✅ Database connection closed")
            except Exception as e:
                print(f"⚠️ Warning during database close: {e}")
        
        # Clean up backup if successful
        if self.backup_path.exists() and self.db_path.exists():
            try:
                self.backup_path.unlink()
                print("🗑️ Backup cleaned up")
            except Exception:
                pass  # Keep backup if cleanup fails

def main():
    """Main function with enhanced setup and monitoring"""
    print("🚀 OPTIMIZED SPENDING INSIGHTS DATABASE SETUP")
    print("="*60)

    db_setup = OptimizedSpendingDatabaseSetup()

    try:
        # Connect with optimizations
        print("🔌 Connecting to database...")
        db_setup.connect()

        # Create optimized schema
        print("📋 Creating optimized database schema...")
        db_setup.create_tables()

        # Insert sample data with options
        use_large_dataset = input("📊 Generate large dataset? (y/N): ").lower().startswith('y')
        print("💾 Inserting sample data...")
        db_setup.insert_sample_data(generate_large_dataset=use_large_dataset)

        # Generate analytics
        print("📊 Generating enhanced analytics...")
        db_setup.generate_optimized_analytics()

        # Optimize database
        db_setup.optimize_database()

        # Display comprehensive statistics
        db_setup.display_enhanced_stats()

        # Generate performance report
        print("\n📈 Generating performance report...")
        perf_report = db_setup.create_performance_report()
        
        # Save performance report
        with open("db_performance_report.json", "w") as f:
            json.dump(perf_report, f, indent=2)
        print("📄 Performance report saved to db_performance_report.json")

        return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

    finally:
        db_setup.close()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 OPTIMIZED DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("🚀 You can now run the enhanced spending insights application.")
        print("📊 Performance monitoring enabled with detailed analytics.")
    else:
        print("\n💥 DATABASE SETUP FAILED!")
        print("🔍 Check the error messages above for troubleshooting.")
