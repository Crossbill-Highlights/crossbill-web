#!/bin/bash

file_path=$(jq -r '.tool_input.file_path' 2>/dev/null)

# Backend Python files
if [[ "$file_path" == *.py ]]; then
  ruff format "$file_path" 2>/dev/null
  ruff check "$file_path" 2>/dev/null
  pyright "$file_path" 2>/dev/null
fi

# Frontend files
if [[ "$file_path" =~ \.(ts|tsx|js|jsx)$ ]]; then
  npm run format -- "$file_path" 2>/dev/null
  npm run lint -- "$file_path" 2>/dev/null
fi

exit 0
