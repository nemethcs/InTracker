#!/bin/bash
# Comprehensive Backend API Test Script

BASE_URL="http://localhost:3000"
EMAIL="testuser@example.com"
PASSWORD="Test123"

echo "🧪 Starting comprehensive backend API tests..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_status=$5
    
    if [ -z "$expected_status" ]; then
        expected_status=200
    fi
    
    echo -n "Testing $name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$url" -H "Authorization: Bearer $TOKEN" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$url" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code, expected $expected_status)"
        echo "  Response: $body" | head -3
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Auth Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. AUTHENTICATION TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -n "Registering user... "
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"name\":\"Test User\"}" 2>&1)

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ User may already exist${NC}"
fi

echo -n "Login... "
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" 2>&1)

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tokens', {}).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ] && [ ${#TOKEN} -gt 50 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Token length: ${#TOKEN})"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Cannot get token"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

test_endpoint "Get current user" "GET" "/auth/me" "" 200

# 2. Projects Tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. PROJECTS TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "List projects" "GET" "/projects" "" 200

PROJECT_DATA='{"name":"Test Project","description":"Test description","status":"active"}'
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/projects" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PROJECT_DATA" 2>&1)

PROJECT_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

if [ -n "$PROJECT_ID" ]; then
    echo -e "${GREEN}✓ Create project PASS${NC} (ID: ${PROJECT_ID:0:8}...)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Create project FAIL${NC}"
    echo "Response: $CREATE_RESPONSE"
    ((TESTS_FAILED++))
    PROJECT_ID=""
fi

if [ -n "$PROJECT_ID" ]; then
    test_endpoint "Get project" "GET" "/projects/$PROJECT_ID" "" 200
    
    test_endpoint "Update project" "PUT" "/projects/$PROJECT_ID" \
        '{"name":"Updated Project","description":"Updated description"}' 200
    
    test_endpoint "List projects (after create)" "GET" "/projects" "" 200
fi

# 3. Features Tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. FEATURES TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$PROJECT_ID" ]; then
    FEATURE_DATA="{\"project_id\":\"$PROJECT_ID\",\"name\":\"Test Feature\",\"description\":\"Test feature description\",\"status\":\"todo\"}"
    CREATE_FEATURE_RESPONSE=$(curl -s -X POST "$BASE_URL/features" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$FEATURE_DATA" 2>&1)
    
    FEATURE_ID=$(echo "$CREATE_FEATURE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
    
    if [ -n "$FEATURE_ID" ]; then
        echo -e "${GREEN}✓ Create feature PASS${NC} (ID: ${FEATURE_ID:0:8}...)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Create feature FAIL${NC}"
        echo "Response: $CREATE_FEATURE_RESPONSE"
        ((TESTS_FAILED++))
        FEATURE_ID=""
    fi
    
    if [ -n "$FEATURE_ID" ]; then
        test_endpoint "Get feature" "GET" "/features/$FEATURE_ID" "" 200
        test_endpoint "List features by project" "GET" "/features/project/$PROJECT_ID" "" 200
        test_endpoint "Update feature" "PUT" "/features/$FEATURE_ID" \
            '{"status":"in_progress"}' 200
        test_endpoint "Get feature todos" "GET" "/features/$FEATURE_ID/todos" "" 200
        test_endpoint "Get feature elements" "GET" "/features/$FEATURE_ID/elements" "" 200
        test_endpoint "Calculate feature progress" "POST" "/features/$FEATURE_ID/calculate-progress" "" 200
    fi
fi

# 4. Elements Tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. ELEMENTS TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$PROJECT_ID" ]; then
    ELEMENT_DATA="{\"project_id\":\"$PROJECT_ID\",\"type\":\"module\",\"title\":\"Test Module\",\"description\":\"Test module description\",\"status\":\"todo\"}"
    CREATE_ELEMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/elements" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$ELEMENT_DATA" 2>&1)
    
    ELEMENT_ID=$(echo "$CREATE_ELEMENT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
    
    if [ -n "$ELEMENT_ID" ]; then
        echo -e "${GREEN}✓ Create element PASS${NC} (ID: ${ELEMENT_ID:0:8}...)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Create element FAIL${NC}"
        echo "Response: $CREATE_ELEMENT_RESPONSE"
        ((TESTS_FAILED++))
        ELEMENT_ID=""
    fi
    
    if [ -n "$ELEMENT_ID" ]; then
        test_endpoint "Get element" "GET" "/elements/$ELEMENT_ID" "" 200
        test_endpoint "Get project elements tree" "GET" "/elements/project/$PROJECT_ID/tree" "" 200
        test_endpoint "Update element" "PUT" "/elements/$ELEMENT_ID" \
            '{"status":"in_progress"}' 200
        test_endpoint "Get element dependencies" "GET" "/elements/$ELEMENT_ID/dependencies" "" 200
    fi
fi

# 5. Todos Tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. TODOS TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$ELEMENT_ID" ] && [ -n "$FEATURE_ID" ]; then
    TODO_DATA="{\"element_id\":\"$ELEMENT_ID\",\"feature_id\":\"$FEATURE_ID\",\"title\":\"Test Todo\",\"description\":\"Test todo description\",\"status\":\"todo\"}"
    CREATE_TODO_RESPONSE=$(curl -s -X POST "$BASE_URL/todos" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$TODO_DATA" 2>&1)
    
    TODO_ID=$(echo "$CREATE_TODO_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
    
    if [ -n "$TODO_ID" ]; then
        echo -e "${GREEN}✓ Create todo PASS${NC} (ID: ${TODO_ID:0:8}...)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Create todo FAIL${NC}"
        echo "Response: $CREATE_TODO_RESPONSE"
        ((TESTS_FAILED++))
        TODO_ID=""
    fi
    
    if [ -n "$TODO_ID" ]; then
        test_endpoint "Get todo" "GET" "/todos/$TODO_ID" "" 200
        test_endpoint "List todos" "GET" "/todos" "" 200
        test_endpoint "Update todo status" "PUT" "/todos/$TODO_ID/status?status=in_progress" "" 200
        test_endpoint "Update todo" "PUT" "/todos/$TODO_ID" \
            '{"title":"Updated Todo","status":"done"}' 200
    fi
fi

# 6. Sessions Tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. SESSIONS TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$PROJECT_ID" ]; then
    SESSION_DATA="{\"project_id\":\"$PROJECT_ID\",\"title\":\"Test Session\",\"goal\":\"Test goal\"}"
    CREATE_SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/sessions" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$SESSION_DATA" 2>&1)
    
    SESSION_ID=$(echo "$CREATE_SESSION_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
    
    if [ -n "$SESSION_ID" ]; then
        echo -e "${GREEN}✓ Create session PASS${NC} (ID: ${SESSION_ID:0:8}...)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Create session FAIL${NC}"
        echo "Response: $CREATE_SESSION_RESPONSE"
        ((TESTS_FAILED++))
        SESSION_ID=""
    fi
    
    if [ -n "$SESSION_ID" ]; then
        test_endpoint "Get session" "GET" "/sessions/$SESSION_ID" "" 200
        test_endpoint "List project sessions" "GET" "/sessions/project/$PROJECT_ID" "" 200
        test_endpoint "Update session" "PUT" "/sessions/$SESSION_ID" \
            '{"notes":"Test notes"}' 200
        
        if [ -n "$TODO_ID" ]; then
            test_endpoint "End session" "POST" "/sessions/$SESSION_ID/end" \
                "{\"todos_completed\":[\"$TODO_ID\"],\"summary\":\"Test session completed\"}" 200
        else
            test_endpoint "End session" "POST" "/sessions/$SESSION_ID/end" \
                '{"summary":"Test session completed"}' 200
        fi
    fi
fi

# 7. Documents Tests
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. DOCUMENTS TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$PROJECT_ID" ]; then
    DOCUMENT_DATA="{\"project_id\":\"$PROJECT_ID\",\"type\":\"architecture\",\"title\":\"Test Document\",\"content\":\"# Test Document\\n\\nThis is a test document.\"}"
    CREATE_DOCUMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/documents" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$DOCUMENT_DATA" 2>&1)
    
    DOCUMENT_ID=$(echo "$CREATE_DOCUMENT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
    
    if [ -n "$DOCUMENT_ID" ]; then
        echo -e "${GREEN}✓ Create document PASS${NC} (ID: ${DOCUMENT_ID:0:8}...)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Create document FAIL${NC}"
        echo "Response: $CREATE_DOCUMENT_RESPONSE"
        ((TESTS_FAILED++))
        DOCUMENT_ID=""
    fi
    
    if [ -n "$DOCUMENT_ID" ]; then
        test_endpoint "Get document" "GET" "/documents/$DOCUMENT_ID" "" 200
        test_endpoint "Get document content" "GET" "/documents/$DOCUMENT_ID/content" "" 200
        test_endpoint "List project documents" "GET" "/documents/project/$PROJECT_ID" "" 200
        test_endpoint "Update document" "PUT" "/documents/$DOCUMENT_ID" \
            '{"content":"# Updated Document\n\nUpdated content."}' 200
    fi
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
echo "Total tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi
