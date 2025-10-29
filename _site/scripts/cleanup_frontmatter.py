import sys, os, re

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Regex to match a ```python fence at top with YAML front-matter inside
    pattern = r'^```python\s*\n(---\s*\ntitle:.*?\nlayout:.*?\nnav_order:.*?\n---)\s*\n```[\r\n]*'
    new_text = re.sub(pattern, r'\1\n', text, flags=re.S | re.M)
    if new_text != text:
        print(f"Cleaned fences in {path}")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)

def main(folder):
    for root, _, files in os.walk(folder):
        for fname in files:
            if fname.endswith('.md'):
                clean_file(os.path.join(root, fname))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: cleanup_frontmatter.py <folder>")
        sys.exit(1)
    main(sys.argv[1])
