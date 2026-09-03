import os
import re

css_path = 'site-lib/styles/obsidian.css'

with open(css_path, 'r') as f:
    content = f.read()

# Make base dark burgundy and deep green
content = re.sub(r'--color-base-00:.*?;', '--color-base-00: #1a0b12;', content)
content = re.sub(r'--color-base-10:.*?;', '--color-base-10: #2a141d;', content)
content = re.sub(r'--color-base-20:.*?;', '--color-base-20: #101c13;', content)
content = re.sub(r'--color-base-25:.*?;', '--color-base-25: #16261b;', content)
content = re.sub(r'--color-base-30:.*?;', '--color-base-30: #1d3324;', content)
content = re.sub(r'--color-base-40:.*?;', '--color-base-40: #2d4a36;', content)
content = re.sub(r'--color-base-50:.*?;', '--color-base-50: #3d6348;', content)

# Make text easier to read with these dark backgrounds
content = re.sub(r'--text-normal:.*?;', '--text-normal: #e0d8de;', content)
content = re.sub(r'--text-muted:.*?;', '--text-muted: #a89fa5;', content)

# Accent color (Gold)
content = re.sub(r'--accent-h:.*?;', '--accent-h: 51;', content)
content = re.sub(r'--accent-s:.*?;', '--accent-s: 100%;', content)
content = re.sub(r'--accent-l:.*?;', '--accent-l: 50%;', content)
content = re.sub(r'--color-accent:.*?;', '--color-accent: #FFD700;', content)
content = re.sub(r'--color-accent-1:.*?;', '--color-accent-1: #FFDF33;', content)
content = re.sub(r'--color-accent-2:.*?;', '--color-accent-2: #FFE666;', content)

# Glow effect on links
if 'text-shadow' not in content:
    content = content.replace('.theme-dark {', '.theme-dark {\n  --link-glow: 0 0 5px rgba(255, 215, 0, 0.4);\n')
    content = content + '\n\na {\n  text-shadow: var(--link-glow);\n}\n\nh1, h2, h3, h4, h5, h6 {\n  text-shadow: 0 0 8px rgba(255, 215, 0, 0.3);\n}\n'

with open(css_path, 'w') as f:
    f.write(content)

print("Styles updated.")
