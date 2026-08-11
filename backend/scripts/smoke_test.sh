#!/bin/bash
#
# Smoke test script for Council Service Management System.
# Runs end-to-end workflow against a running dev server.
# Usage: ./scripts/smoke_test.sh [BASE_URL]
#

set -uo pipefail

BASE_URL="${1:-http://127.0.0.1:5000}"
API_PREFIX="/api/v1"
DELIM=$'\x1f'

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

ADMIN_TOKEN=""
OFFICER_TOKEN=""
OFFICER_EMAIL=""
REQUEST_ID=""
OFFICER_ID=""

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

RESPONSE_BODY=""
HTTP_STATUS=""

print_pass() {
    local test_name="$1"
    local details="${2:-}"
    if [[ -n "$details" ]]; then
        echo -e "${GREEN}✓ PASS:${RESET} $test_name — $details"
    else
        echo -e "${GREEN}✓ PASS:${RESET} $test_name"
    fi
}

print_fail() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"
    local details="${4:-}"
    echo -e "${RED}✗ FAIL:${RESET} $test_name"
    echo -e "  Expected: $expected"
    echo -e "  Actual:   $actual"
    if [[ -n "$details" ]]; then
        echo -e "  Details:  $details"
    fi
}

# ---- API Call ----
# Prints "STATUS<DELIM>BODY" to stdout. Caller must capture and split it.
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"
    local header_value="${4:-}"

    local url="${BASE_URL}${API_PREFIX}${endpoint}"
    local tmp_body
    tmp_body=$(mktemp)

    local curl_args=(-s -o "$tmp_body" -w '%{http_code}' -X "$method" "$url")

    if [[ -n "$data" ]]; then
        curl_args+=(-H "Content-Type: application/json")
    fi
    if [[ -n "$header_value" ]]; then
        curl_args+=(-H "$header_value")
    fi
    if [[ -n "$data" ]]; then
        curl_args+=(-d "$data")
    fi

    local status body
    status=$(curl "${curl_args[@]}" 2>/dev/null)
    body=$(cat "$tmp_body")
    rm -f "$tmp_body"

    printf '%s%s%s' "$status" "$DELIM" "$body"
}

# Runs api_call and sets HTTP_STATUS / RESPONSE_BODY in the caller's real shell.
do_call() {
    local result
    result=$(api_call "$@")
    HTTP_STATUS="${result%%"$DELIM"*}"
    RESPONSE_BODY="${result#*"$DELIM"}"
}

login() {
    local email="$1"
    local password="$2"
    local token_var_name="$3"

    echo -e "${BLUE}➤${RESET} Logging in as $email..."
    local payload
    payload=$(jq -n --arg email "$email" --arg password "$password" \
        '{email: $email, password: $password}')

    do_call POST /auth/login "$payload"

    if [[ "$HTTP_STATUS" -eq 200 ]]; then
        local token
        token=$(echo "$RESPONSE_BODY" | jq -r '.access_token')
        printf -v "$token_var_name" '%s' "$token"
        echo -e "${GREEN}✓${RESET} Login successful"
        return 0
    else
        echo -e "${RED}✗${RESET} Login failed (status $HTTP_STATUS): $RESPONSE_BODY"
        return 1
    fi
}

create_user() {
    local admin_token="$1"
    local full_name="$2"
    local email="$3"
    local password="$4"
    local role="$5"
    local department_id="${6:-}"

    local payload
    if [[ -n "$department_id" ]]; then
        payload=$(jq -n \
            --arg full_name "$full_name" --arg email "$email" \
            --arg password "$password" --arg role "$role" \
            --argjson department_id "$department_id" \
            '{full_name: $full_name, email: $email, password: $password, role: $role, department_id: $department_id}')
    else
        payload=$(jq -n \
            --arg full_name "$full_name" --arg email "$email" \
            --arg password "$password" --arg role "$role" \
            '{full_name: $full_name, email: $email, password: $password, role: $role}')
    fi

    do_call POST /admin/users "$payload" "Authorization: Bearer $admin_token"

    if [[ "$HTTP_STATUS" -eq 201 ]]; then
        echo "$RESPONSE_BODY" | jq -r '.user_id'
        return 0
    else
        echo -e "${RED}✗${RESET} User creation failed (status $HTTP_STATUS): $RESPONSE_BODY" >&2
        return 1
    fi
}

assert_status() {
    local expected="$1"
    local test_name="$2"
    local details="${3:-}"

    ((TESTS_TOTAL++))

    if [[ "$HTTP_STATUS" -eq "$expected" ]]; then
        print_pass "$test_name" "$details"
        ((TESTS_PASSED++))
        return 0
    else
        print_fail "$test_name" "$expected" "$HTTP_STATUS" "$RESPONSE_BODY"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_json_field() {
    local field="$1"
    local expected="$2"
    local test_name="${3:-JSON field '$field' equals '$expected'}"

    local actual
    actual=$(echo "$RESPONSE_BODY" | jq -r "$field" 2>/dev/null)

    ((TESTS_TOTAL++))
    if [[ "$actual" == "$expected" ]]; then
        print_pass "$test_name" "Field '$field' = '$actual'"
        ((TESTS_PASSED++))
        return 0
    else
        print_fail "$test_name" "$expected" "$actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_json_array_non_empty() {
    local test_name="$1"
    local array_path="${2:-.}"
    local count
    count=$(echo "$RESPONSE_BODY" | jq "$array_path | length" 2>/dev/null)

    ((TESTS_TOTAL++))
    if [[ -n "$count" && "$count" -gt 0 ]]; then
        print_pass "$test_name" "Array has $count entries"
        ((TESTS_PASSED++))
        return 0
    else
        print_fail "$test_name" "Non-empty array" "${count:-0} entries"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_smoke_workflow() {
    echo -e "\n${BLUE}=== Smoke Test: Full Workflow ===${RESET}\n"

    echo -e "${BLUE}➤${RESET} Admin login..."
    if ! login "admin@council.gov" "admin123" "ADMIN_TOKEN"; then
        echo -e "${RED}✗ Aborting: admin login failed${RESET}"
        return 1
    fi

    OFFICER_EMAIL="officer.smoke.$(date +%s)_$RANDOM@council.gov"
    echo -e "\n${BLUE}➤${RESET} Creating officer user: $OFFICER_EMAIL"
    OFFICER_ID=$(create_user "$ADMIN_TOKEN" "Smoke Officer" "$OFFICER_EMAIL" "officer12345" "SUPPORT_OFFICER" "1")
    if [[ -z "$OFFICER_ID" || "$OFFICER_ID" == "null" ]]; then
        echo -e "${RED}✗ Aborting: failed to create officer${RESET}"
        return 1
    fi
    echo -e "${GREEN}✓${RESET} Officer created (ID: $OFFICER_ID)"

    echo -e "\n${BLUE}➤${RESET} Officer login..."
    if ! login "$OFFICER_EMAIL" "officer12345" "OFFICER_TOKEN"; then
        echo -e "${RED}✗ Aborting: officer login failed${RESET}"
        return 1
    fi

    # ---- Happy Path ----
    # Guest submission — no account dependency, exercises the public path
    echo -e "\n${BLUE}➤${RESET} Guest submits a request..."
    local request_data
    request_data=$(jq -n '{title:"Smoke Test Request", description:"This is a smoke test request", location:"Smoke Street 123", category:"ROADS", guest_name:"Smoke Guest", guest_email:"guest.smoke@example.com", guest_phone:"07000000000"}')
    do_call POST /requests "$request_data"
    assert_status 201 "Guest submits request"
    if [[ "$HTTP_STATUS" -eq 201 ]]; then
        REQUEST_ID=$(echo "$RESPONSE_BODY" | jq -r '.request_id')
        echo -e "  Request ID: $REQUEST_ID"
        assert_json_field ".title" "Smoke Test Request"
        assert_json_field ".status" "SUBMITTED"
        assert_json_field ".priority" "MEDIUM"
    fi

    echo -e "\n${BLUE}➤${RESET} Officer self-assigns..."
    local assign_data
    assign_data=$(jq -n --argjson id "$OFFICER_ID" '{assigned_officer_id: $id}')
    do_call PATCH "/requests/$REQUEST_ID/assign" "$assign_data" "Authorization: Bearer $OFFICER_TOKEN"
    assert_status 200 "Officer self-assigns"
    assert_json_field ".assigned_officer.user_id" "$OFFICER_ID"

    echo -e "\n${BLUE}➤${RESET} Officer moves to UNDER_REVIEW..."
    do_call PATCH "/requests/$REQUEST_ID/status" '{"status":"UNDER_REVIEW"}' "Authorization: Bearer $OFFICER_TOKEN"
    assert_status 200 "Officer sets UNDER_REVIEW"
    assert_json_field ".status" "UNDER_REVIEW"

    echo -e "\n${BLUE}➤${RESET} Officer moves to IN_PROGRESS..."
    do_call PATCH "/requests/$REQUEST_ID/status" '{"status":"IN_PROGRESS"}' "Authorization: Bearer $OFFICER_TOKEN"
    assert_status 200 "Officer sets IN_PROGRESS"
    assert_json_field ".status" "IN_PROGRESS"

    echo -e "\n${BLUE}➤${RESET} Admin resolves the request..."
    do_call PATCH "/requests/$REQUEST_ID/status" '{"status":"RESOLVED"}' "Authorization: Bearer $ADMIN_TOKEN"
    assert_status 200 "Admin resolves request"
    assert_json_field ".status" "RESOLVED"

    echo -e "\n${BLUE}➤${RESET} Admin closes the request..."
    do_call PATCH "/requests/$REQUEST_ID/status" '{"status":"CLOSED"}' "Authorization: Bearer $ADMIN_TOKEN"
    assert_status 200 "Admin closes request"
    assert_json_field ".status" "CLOSED"

    echo -e "\n${BLUE}➤${RESET} Officer adds a note..."
    local note_body="This request has been processed via smoke test."
    local note_data
    note_data=$(jq -n --arg body "$note_body" '{body: $body}')
    do_call POST "/requests/$REQUEST_ID/notes" "$note_data" "Authorization: Bearer $OFFICER_TOKEN"
    assert_status 201 "Officer adds note"
    assert_json_field ".body" "$note_body"

    echo -e "\n${BLUE}➤${RESET} Admin views notes..."
    do_call GET "/requests/$REQUEST_ID/notes" "" "Authorization: Bearer $ADMIN_TOKEN"
    assert_status 200 "Admin views notes"
    assert_json_array_non_empty "Notes list is not empty" "."

    echo -e "\n${BLUE}➤${RESET} Admin views audit log..."
    do_call GET "/requests/$REQUEST_ID/audit" "" "Authorization: Bearer $ADMIN_TOKEN"
    assert_status 200 "Admin views audit log"
    assert_json_array_non_empty "Audit log has entries" ".data"

    # ---- Negative Checks (no-auth, since we no longer depend on a resident account) ----
    echo -e "\n${BLUE}➤${RESET} No-auth request tries to change status (should fail)..."
    do_call PATCH "/requests/$REQUEST_ID/status" '{"status":"UNDER_REVIEW"}'
    assert_status 401 "Unauthenticated request blocked from status change"

    echo -e "\n${BLUE}➤${RESET} No-auth request tries to view notes (should fail)..."
    do_call GET "/requests/$REQUEST_ID/notes"
    assert_status 401 "Unauthenticated request blocked from viewing notes"

    echo -e "\n${BLUE}➤${RESET} Officer tries to assign a resident as officer (should fail)..."
    # user_id 2 is expected to be a non-officer account from seed data
    local assign_bad_data
    assign_bad_data=$(jq -n '{assigned_officer_id: 2}')
    do_call PATCH "/requests/$REQUEST_ID/assign" "$assign_bad_data" "Authorization: Bearer $ADMIN_TOKEN"
    assert_status 400 "Admin cannot assign non-officer as officer"

    echo -e "\n${BLUE}✓ Smoke test workflow completed${RESET}"
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "           TEST SUMMARY"
    echo "=========================================="
    echo -e "Total:  ${TESTS_TOTAL}"
    echo -e "Passed: ${GREEN}${TESTS_PASSED}${RESET}"
    echo -e "Failed: ${RED}${TESTS_FAILED}${RESET}"
    echo "=========================================="

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${RESET}"
        return 0
    else
        echo -e "${RED}Some tests failed.${RESET}"
        return 1
    fi
}

main() {
    echo -e "${BLUE}Council Service Management System - Smoke Test${RESET}"
    echo -e "Base URL: $BASE_URL"

    echo -e "\n${BLUE}➤${RESET} Checking server availability..."
    if curl -s -o /dev/null "$BASE_URL" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${RESET} Server is reachable at $BASE_URL"
    else
        echo -e "${RED}✗${RESET} Server not reachable at $BASE_URL"
        exit 1
    fi

    test_smoke_workflow
    print_summary
    exit $?
}

main "$@"