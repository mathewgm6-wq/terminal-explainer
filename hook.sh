#!/bin/bash

trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG

PROMPT_COMMAND='
exit_code=$?;
if [ $exit_code -ne 0 ]; then
    response=$(curl -s -X POST http://localhost:5000/explain \
    -H "Content-Type: application/json" \
    -d "{\"error\": \"Command: $last_command\"}")

    echo ""
    echo "💡 AI Fix:"
    echo "$response"
fi
'