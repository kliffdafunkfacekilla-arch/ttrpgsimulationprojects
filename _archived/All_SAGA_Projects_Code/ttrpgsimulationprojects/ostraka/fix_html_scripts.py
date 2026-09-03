import os
import glob
import re

html_files = glob.glob('**/*.html', recursive=True)

count = 0
for file in html_files:
    if 'site-lib' in file: continue

    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Let's replace the script entirely
    new_content = re.sub(
        r'<script>.*?localStorage\.getItem.*?matchMedia.*?classList\.add\(theme\);.*?</script>',
        "<script>let theme = 'dark'; document.body.classList.remove('theme-light'); document.body.classList.add('theme-dark');</script>",
        content,
        flags=re.DOTALL
    )

    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        count += 1

print(f"Updated {count} HTML files to replace the theme script completely.")
