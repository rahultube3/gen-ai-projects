import duckdb
import os

def check_transaction(txn_id: str):
    # Get database path from environment or use default
    db_path = os.getenv('DATABASE_PATH', 'data/bank.db')
    
    conn = duckdb.connect(db_path)

    txn = conn.execute("SELECT * FROM transactions WHERE txn_id = ?", (txn_id,)).fetchone()
    if not txn:
        conn.close()
        return {"error": "Transaction not found"}

    txn_dict = {
        "txn_id": txn[0],
        "customer_id": txn[1],
        "amount": txn[2],
        "location": txn[3],
        "timestamp": txn[4],
    }

    customer = conn.execute("SELECT * FROM customer_profiles WHERE customer_id = ?", (txn[1],)).fetchone()
    if not customer:
        conn.close()
        return {"error": "Customer profile not found"}

    customer_dict = {
        "customer_id": customer[0],
        "name": customer[1],
        "age": customer[2],
        "risk_score": customer[3]
    }

    conn.close()

    # Simple risk logic
    score = customer_dict["risk_score"]
    if txn_dict["amount"] > 3000:
        score += 0.3
    if txn_dict["location"] != "HomeCity":  # Assume 'HomeCity' is safe
        score += 0.2

    return {
        "txn_id": txn_id,
        "customer_id": txn_dict["customer_id"],
        "fraud_score": round(score, 2),
        "risk_level": "High" if score > 0.5 else "Low",
        "reasoning": "High amount and/or unfamiliar location"
    }
