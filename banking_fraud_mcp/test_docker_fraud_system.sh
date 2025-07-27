#!/bin/bash

# Docker Banking Fraud Detection System Test Suite
# Comprehensive testing script for validating the ML fraud detection system

echo "🚀 DOCKER BANKING FRAUD DETECTION TEST SUITE"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DOCKER_IMAGE="banking_fraud_mcp-fraud-detection"
TEST_RESULTS=()

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}🔍 Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        TEST_RESULTS+=("PASS: $test_name")
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        TEST_RESULTS+=("FAIL: $test_name")
    fi
    echo ""
}

# Test 1: Docker Image Availability
run_test "Docker Image Availability" "docker images | grep -q banking_fraud_mcp"

# Test 2: Container Build Capability
run_test "Container Build Test" "./docker-manage.sh build > /dev/null 2>&1"

# Test 3: Basic Container Run
run_test "Basic Container Execution" "docker run --rm $DOCKER_IMAGE echo 'Container runs successfully' > /dev/null 2>&1"

# Test 4: ML System Loading
run_test "ML System Loading" "docker run --rm -e DATABASE_PATH=/app/data/bank.db $DOCKER_IMAGE uv run python -c 'from ml_fraud_detector import get_ml_detector; get_ml_detector(); print(\"ML System OK\")' > /dev/null 2>&1"

# Test 5: Database Connection
run_test "Database Connection" "docker run --rm -e DATABASE_PATH=/app/data/bank.db $DOCKER_IMAGE uv run python -c 'import duckdb, os; conn = duckdb.connect(os.getenv(\"DATABASE_PATH\")); print(conn.execute(\"SELECT COUNT(*) FROM transactions\").fetchone()[0], \"transactions found\"); conn.close()' > /dev/null 2>&1"

# Test 6: Fraud Detection Function
run_test "Fraud Detection Function" "docker run --rm -e DATABASE_PATH=/app/data/bank.db $DOCKER_IMAGE uv run python -c 'from ml_fraud_detector import check_transaction_ml; result = check_transaction_ml(\"txn001\"); print(\"Fraud detection:\", result[\"ml_analysis\"][\"model_prediction\"])' > /dev/null 2>&1"

# Test 7: Multiple Transaction Processing
run_test "Multiple Transaction Processing" "docker run --rm -e DATABASE_PATH=/app/data/bank.db $DOCKER_IMAGE uv run python -c 'from ml_fraud_detector import check_transaction_ml; [check_transaction_ml(f\"txn{i:03d}\") for i in [1, 21, 31]]; print(\"Multi-transaction processing OK\")' > /dev/null 2>&1"

# Test 8: Performance Test (< 1 second average)
run_test "Performance Benchmark" "docker run --rm -e DATABASE_PATH=/app/data/bank.db $DOCKER_IMAGE uv run python -c 'import time; from ml_fraud_detector import check_transaction_ml; start=time.time(); [check_transaction_ml(\"txn001\") for _ in range(3)]; avg_time=(time.time()-start)/3; print(f\"Avg time: {avg_time:.3f}s\"); exit(0 if avg_time < 1.0 else 1)' > /dev/null 2>&1"

# Test 9: Health Check Script
run_test "Health Check Script" "docker run --rm -e DATABASE_PATH=/app/data/bank.db $DOCKER_IMAGE uv run python /app/healthcheck.py > /dev/null 2>&1"

# Test 10: Memory Usage (Container should start with reasonable memory)
run_test "Container Resource Usage" "docker run --rm --memory=1g -e DATABASE_PATH=/app/data/bank.db $DOCKER_IMAGE uv run python -c 'from ml_fraud_detector import get_ml_detector; get_ml_detector(); print(\"Memory usage OK\")' > /dev/null 2>&1"

echo ""
echo "📊 TEST RESULTS SUMMARY"
echo "======================="

passed=0
failed=0

for result in "${TEST_RESULTS[@]}"; do
    if [[ $result == PASS* ]]; then
        echo -e "${GREEN}$result${NC}"
        ((passed++))
    else
        echo -e "${RED}$result${NC}"
        ((failed++))
    fi
done

echo ""
echo "📈 STATISTICS:"
echo "   Total Tests: $((passed + failed))"
echo -e "   ${GREEN}Passed: $passed${NC}"
echo -e "   ${RED}Failed: $failed${NC}"

if [ $failed -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Your Docker Banking Fraud Detection System is fully operational!${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed. Please check the system configuration.${NC}"
    exit 1
fi
