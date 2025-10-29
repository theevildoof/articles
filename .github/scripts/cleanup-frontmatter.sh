#!/usr/bin/env bash
# cleanup-frontmatter.sh
# Usage: cleanup-frontmatter.sh <file>

file="$1"

if [[ ! -f "$file" ]]; then
  echo "File not found: $file" >&2
  exit 1
fi

# Remove leading blank lines
# Then if the first non-blank is ```python, process accordingly
tmp="${file}.tmp"
awk '
  BEGIN { skip = 1 }
  {
    if (skip && /^[[:space:]]*$/) {
      # still skipping blank lines
      next
    }
    skip = 0
    print
  }' "$file" > "$tmp"

mv "$tmp" "$file"

# Now handle fenced YAML at the top
first=$(head -n1 "$file")
if [[ "$first" == '```python'* ]]; then
  echo "Fixing front matter in $file"
  # Remove the first ```python line
  tail -n +2 "$file" > "${file}.tmp"

  # Now remove the trailing ``` after YAML block
  awk '
    BEGIN { done = 0 }
    {
      if (!done && /^---$/ && had_first) {
        # found end of YAML block
        next_line = 1
      }
      if (!had_first && /^---$/) {
        had_first = 1
        print
        next
      }
      if (had_first && next_line && /^```$/) {
        done = 1
        next
      }
      { print }
    }' "${file}.tmp" > "$tmp"

  mv "$tmp" "$file"
fi
