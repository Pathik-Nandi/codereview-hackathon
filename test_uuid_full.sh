#!/bin/bash

# Test UUID Authentication System
# ===============================

BASE_URL="http://localhost:5000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Starting Flask server..."
cd /home/maheshrv/Documents/IGOT/sourcecodes-igot/codereview
export FLASK_DEBUG=0
python3 main.py > /tmp/flask_uuid_test.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to start
sleep 8

echo -e "\n=== Testing UUID Authentication System ==="

# Test 1: Health Check
echo -e "\n1. Health Check"
RESPONSE=$(curl -s -w "\n%{http_code}" ${BASE_URL}/health)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (HTTP $HTTP_CODE)${NC}"
fi

# Test 2: Register User
echo -e "\n2. Register User (UUID)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "username": "uuiduser",
        "email": "uuid@example.com",
        "password": "TestPass123!",
        "full_name": "UUID Test User"
    }')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "201" ]; then
    echo -e "${GREEN}✓ Registration successful${NC}"
    echo "$BODY" | python3 -m json.tool
    USER_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['user_id'])")
    echo -e "User ID (UUID): ${GREEN}$USER_ID${NC}"
else
    echo -e "${RED}✗ Registration failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
fi

# Test 3: Login
echo -e "\n3. Login with UUID user"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "email": "uuid@example.com",
        "password": "TestPass123!"
    }')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    TOKEN=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['session']['token'])")
    SESSION_USER_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['session']['user_id'])")
    echo -e "Session User ID (UUID): ${GREEN}$SESSION_USER_ID${NC}"
    echo "Token (first 50 chars): ${TOKEN:0:50}..."
else
    echo -e "${RED}✗ Login failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
fi

# Test 4: Validate Token
echo -e "\n4. Validate Token"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${BASE_URL}/api/auth/validate" \
    -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Token validation successful${NC}"
    VALIDATED_USER_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['user_id'])")
    echo -e "Validated User ID (UUID): ${GREEN}$VALIDATED_USER_ID${NC}"
else
    echo -e "${RED}✗ Token validation failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
fi

# Clean up
echo -e "\n=== Cleanup ===" 
kill $SERVER_PID 2>/dev/null
echo "Server stopped"

echo -e "\n=== UUID Verification in Database ==="
PGPASSWORD=postgres psql -U postgres -h localhost -d pr_analysis -p 5433 -c "SELECT id, username, email FROM users WHERE email='uuid@example.com';"
