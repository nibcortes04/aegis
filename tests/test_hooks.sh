#!/usr/bin/env bash
set -euo pipefail

# End-to-end Hook Contract Verification Test
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HOOK_SCRIPT="$REPO_ROOT/scripts/agy_hook_handler.py"
export AGY_HOOK_SILENT=1

echo "=== Running AGY Hook Contract Tests ==="

# 1. Test PreToolUse with safe tool (view_file) -> Must return decision: "allow"
echo -n "Test 1: PreToolUse safe tool (view_file) -> "
INPUT_JSON='{"hookEventName":"PreToolUse","toolCall":{"name":"view_file","args":{"AbsolutePath":"/tmp/test.txt"}}}'
OUTPUT=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
DECISION=$(echo "$OUTPUT" | jq -r '.decision')
if [ "$DECISION" == "allow" ]; then
    echo "PASS (decision: $DECISION)"
else
    echo "FAIL (expected 'allow', got '$DECISION')"
    exit 1
fi

# 2. Test PreToolUse with critical command (rm -rf) -> Two-Factor Safety Gate (deny -> ask)
echo -n "Test 2a: PreToolUse critical command Step 1 (rm -rf) -> "
INPUT_JSON='{"hookEventName":"PreToolUse","toolCall":{"name":"run_command","args":{"CommandLine":"rm -rf /tmp/data_test_double_confirm"}}}'
OUTPUT=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
DECISION=$(echo "$OUTPUT" | jq -r '.decision')
if [ "$DECISION" == "deny" ]; then
    echo "PASS (decision: $DECISION - Step 1 blocked)"
else
    echo "FAIL (expected 'deny', got '$DECISION')"
    exit 1
fi

echo -n "Test 2b: PreToolUse critical command Step 2 within TTL -> "
OUTPUT2=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
DECISION2=$(echo "$OUTPUT2" | jq -r '.decision')
if [ "$DECISION2" == "ask" ]; then
    echo "PASS (decision: $DECISION2 - Step 2 elevated to human prompt)"
else
    echo "FAIL (expected 'ask', got '$DECISION2')"
    exit 1
fi

# 3. Test PreToolUse with safe command (git status) -> Must return decision: "allow"
echo -n "Test 3: PreToolUse safe command (git status) -> "
INPUT_JSON='{"hookEventName":"PreToolUse","toolCall":{"name":"run_command","args":{"CommandLine":"git status"}}}'
OUTPUT=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
DECISION=$(echo "$OUTPUT" | jq -r '.decision')
if [ "$DECISION" == "allow" ]; then
    echo "PASS (decision: $DECISION)"
else
    echo "FAIL (expected 'allow', got '$DECISION')"
    exit 1
fi

# 4. Test Stop event -> Must return valid JSON (no error)
echo -n "Test 4: Stop event contract -> "
INPUT_JSON='{"hookEventName":"Stop","terminationReason":"model_stop","fullyIdle":true}'
OUTPUT=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
echo "PASS (output: $OUTPUT)"

# 5. Test empty input resilience -> Must exit cleanly without throwing unhandled exception
echo -n "Test 5: Empty input fallback -> "
OUTPUT=$(echo "" | python3 "$HOOK_SCRIPT")
echo "PASS (clean exit)"

# 6. Test ask_question -> Must return decision: "allow"
echo -n "Test 6: PreToolUse ask_question -> "
INPUT_JSON='{"hookEventName":"PreToolUse","toolCall":{"name":"ask_question","args":{"questions":[]}}}'
OUTPUT=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
DECISION=$(echo "$OUTPUT" | jq -r '.decision')
if [ "$DECISION" == "allow" ]; then
    echo "PASS (decision: $DECISION)"
else
    echo "FAIL (expected 'allow', got '$DECISION')"
    exit 1
fi

# 7. Test PreToolUse write_to_file in plan mode -> Must return decision: "ask"
echo -n "Test 7: PreToolUse write_to_file in plan mode -> "
INPUT_JSON='{"hookEventName":"PreToolUse","cycle_mode":"plan","toolCall":{"name":"write_to_file","args":{"TargetFile":"/tmp/test.txt","CodeContent":""}}}'
OUTPUT=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
DECISION=$(echo "$OUTPUT" | jq -r '.decision')
if [ "$DECISION" == "ask" ]; then
    echo "PASS (decision: $DECISION)"
else
    echo "FAIL (expected 'ask', got '$DECISION')"
    exit 1
fi

echo "=== All AGY Hook Contract Tests Passed! ==="
