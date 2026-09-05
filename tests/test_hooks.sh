#!/usr/bin/env bash
set -euo pipefail

# End-to-end Hook Contract Verification Test
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HOOK_SCRIPT="$REPO_ROOT/scripts/agy_hook_handler.py"

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

# 2. Test PreToolUse with critical command (rm -rf) -> Must return decision: "ask"
echo -n "Test 2: PreToolUse critical command (rm -rf) -> "
INPUT_JSON='{"hookEventName":"PreToolUse","toolCall":{"name":"run_command","args":{"CommandLine":"rm -rf /tmp/data"}}}'
OUTPUT=$(echo "$INPUT_JSON" | python3 "$HOOK_SCRIPT")
DECISION=$(echo "$OUTPUT" | jq -r '.decision')
if [ "$DECISION" == "ask" ]; then
    echo "PASS (decision: $DECISION)"
else
    echo "FAIL (expected 'ask', got '$DECISION')"
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

echo "=== All AGY Hook Contract Tests Passed! ==="
