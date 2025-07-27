#!/usr/bin/env python3
"""
Model Validation Script
Test the retrained model against known risk level transactions
"""

import asyncio
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_model_performance():
    """Test model performance across all risk levels"""
    
    print("🧪 FRAUD MODEL VALIDATION TEST")
    print("=" * 50)
    
    # Test cases with expected risk levels
    test_cases = [
        # MINIMAL risk transactions
        ("txn001", "MINIMAL", "Coffee purchase at HomeCity"),
        ("txn002", "MINIMAL", "Lunch at local restaurant"),
        ("txn003", "MINIMAL", "Small grocery purchase"),
        
        # LOW risk transactions  
        ("txn004", "LOW", "Shopping mall purchase"),
        ("txn010", "LOW", "Gas station fill-up"),
        ("txn015", "LOW", "Department store purchase"),
        
        # MEDIUM risk transactions
        ("txn020", "MEDIUM", "Late night restaurant"),
        ("txn025", "MEDIUM", "Travel booking"),
        ("txn030", "MEDIUM", "Higher amount shopping"),
        
        # HIGH risk transactions
        ("txn040", "HIGH", "Casino transaction"),
        ("txn045", "HIGH", "Cryptocurrency purchase"),
        ("txn050", "HIGH", "Large amount unusual location"),
        
        # CRITICAL risk transactions
        ("txn070", "CRITICAL", "Offshore transaction"),
        ("txn075", "CRITICAL", "Money laundering pattern"),
        ("txn080", "CRITICAL", "Shell company transaction"),
    ]
    
    results = []
    
    @asynccontextmanager
    async def create_server_session():
        server_params = StdioServerParameters(
            command="uv", 
            args=["run", "python", "fraud_server.py"],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async with create_server_session() as session:
        print(f"🔍 Testing {len(test_cases)} transactions...")
        
        for txn_id, expected_level, description in test_cases:
            try:
                # Analyze transaction
                result = await session.call_tool(
                    "check_fraud",
                    arguments={"txn_id": txn_id}
                )
                
                # Parse result
                analysis = result.content[0].text
                
                # Extract key metrics
                score_line = [line for line in analysis.split('\n') if 'Fraud Score:' in line]
                risk_line = [line for line in analysis.split('\n') if 'Risk Level:' in line]
                
                if score_line and risk_line:
                    score = float(score_line[0].split('Fraud Score:')[1].strip())
                    actual_level = risk_line[0].split('Risk Level:')[1].strip()
                    
                    # Determine if classification is correct
                    correct = actual_level == expected_level
                    status = "✅" if correct else "❌"
                    
                    results.append({
                        'txn_id': txn_id,
                        'expected': expected_level,
                        'actual': actual_level,
                        'score': score,
                        'correct': correct,
                        'description': description
                    })
                    
                    print(f"{status} {txn_id}: {score:.3f} -> {actual_level} (expected {expected_level})")
                else:
                    print(f"❌ {txn_id}: Failed to parse analysis")
                    
            except Exception as e:
                print(f"❌ {txn_id}: Error - {e}")
    
    # Calculate accuracy
    if results:
        correct_count = sum(1 for r in results if r['correct'])
        total_count = len(results)
        accuracy = correct_count / total_count * 100
        
        print("\n📊 VALIDATION RESULTS:")
        print(f"   Accuracy: {accuracy:.1f}% ({correct_count}/{total_count})")
        
        # Group by risk level
        by_level = {}
        for r in results:
            level = r['expected']
            if level not in by_level:
                by_level[level] = {'correct': 0, 'total': 0}
            by_level[level]['total'] += 1
            if r['correct']:
                by_level[level]['correct'] += 1
        
        print("\n🎯 ACCURACY BY RISK LEVEL:")
        for level in ['MINIMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            if level in by_level:
                stats = by_level[level]
                level_accuracy = stats['correct'] / stats['total'] * 100
                print(f"   {level}: {level_accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        # Show misclassifications
        misclassified = [r for r in results if not r['correct']]
        if misclassified:
            print("\n⚠️ MISCLASSIFICATIONS:")
            for r in misclassified:
                print(f"   {r['txn_id']}: {r['actual']} (expected {r['expected']}) - {r['description']}")
        
        print(f"\n🎉 Model validation completed!")
        if accuracy >= 80:
            print("✅ Model performance is EXCELLENT!")
        elif accuracy >= 60:
            print("⚠️ Model performance is GOOD but could be improved")
        else:
            print("❌ Model performance needs improvement")

if __name__ == "__main__":
    asyncio.run(test_model_performance())
