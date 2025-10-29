#!/usr/bin/env bash
# cleanup-frontmatter.sh
# Usage: cleanup-frontmatter.sh <file>

file="$1"

if [[ ! -f "$file" ]]; then
  echo "File not found: $file" >&2
  exit 1
fi

# Read first 5 lines to check for ```python then YAML then ```
first_line=$(head -n1 "$file")
if [[ "$first_line" == '```python'* ]]; then
  echo "Fixing front matter in $file"
  # Remove the first line (```python), then remove the trailing ``` after front matter
  # Approach: skip the first line, then drop the ``` line at the end of YAML block
  awk ' 
    NR==1 {next} 
    /^---$/ && !found { print; found=1; next } 
    found && /^```$/ { exit } 
    { print } 
    END { if (!found) exit 1 } ' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
else
  # nothing to do
  #echo "No fenced YAML found in $file"
  :
fi
