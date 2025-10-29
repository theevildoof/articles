#!/usr/bin/env bash
# cleanup_frontmatter_trim.sh
# Usage: cleanup_frontmatter_trim.sh <file>

file="$1"
if [[ ! -f "$file" ]]; then
  echo "ERROR: File not found: $file" >&2
  exit 1
fi

# Extract only lines 4 to 8 and then append the rest after line 8 (optional; if you really want just 4-8 only then skip append)
# If you want only 4-8: 
sed -n '4,8p;10,$p' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"


# If you want to keep 4-8 then everything else after 8:
# (uncomment and use this instead of the above)
# (sed -n '4,8p;9,$p' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file")

echo "Trimmed $file to lines 4-8"
