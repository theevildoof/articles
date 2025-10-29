#!/usr/bin/env bash
# cleanup_frontmatter.sh
# Usage: cleanup_frontmatter.sh <file>

file="$1"

if [[ ! -f "$file" ]]; then
  echo "File not found: $file" >&2
  exit 1
fi

# Create a tmp file
tmp="${file}.tmp"

# 1) Remove leading blank lines
awk '
  BEGIN { skip = 1 }
  {
    if (skip && /^[[:space:]]*$/) {
      next
    }
    skip = 0
    print
  }' "$file" > "$tmp"

mv "$tmp" "$file"

# 2) Check if first non-blank line is a code fence ```python (or ``` python)
first_line=$(head -n1 "$file")
if [[ "$first_line" =~ ^\`\`\`[[:space:]]*python ]]; then
  echo "➡ Removing leading ```python fence in $file"

  # Remove that first fence line
  tail -n +2 "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"

  # Now remove the trailing ``` that ends the fenced block *if* it comes right after YAML
  awk '
    BEGIN { in_front = 0 }
    {
      if (NR==1 && /^---/) {
        in_front=1
        print
        next
      }
      if (in_front && /^---$/) {
        print
        in_front = 2
        next
      }
      if (in_front==2 && /^\`\`\`[[:space:]]*$/) {
        # skip this trailing fence line
        next
      }
      print
    }' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"

  # Ensure no more code-fence at very top:
  # If the first line is ``` (without python) remove it too
  first_line2=$(head -n1 "$file")
  if [[ "$first_line2" =~ ^\`\`\` ]]; then
    echo "➡ Removing extra leading fence in $file"
    tail -n +2 "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
  fi

else
  echo "No leading ```python fence found in $file"
fi
