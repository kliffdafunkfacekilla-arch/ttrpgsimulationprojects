import re

css_path = 'site-lib/styles/obsidian.css'
with open(css_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Specifically target the .theme-dark block to insert our colors
dark_theme_insertion = """
.theme-dark {
  --color-base-00: #1a0b12; /* Dark burgundy */
  --color-base-10: #2a141d;
  --color-base-20: #101c13; /* Deep forest green */
  --color-base-25: #16261b;
  --color-base-30: #1d3324;
  --color-base-40: #2d4a36;
  --color-base-50: #3d6348;

  --text-normal: #e0d8de;
  --text-muted: #a89fa5;

  --accent-h: 51;
  --accent-s: 100%;
  --accent-l: 50%;
  --color-accent: #FFD700; /* Gold */
  --color-accent-1: #FFDF33;
  --color-accent-2: #FFE666;

  --link-glow: 0 0 5px rgba(255, 215, 0, 0.4);
"""

# Replace the beginning of .theme-dark { with our customized block
new_content = re.sub(r'\.theme-dark\s*\{', dark_theme_insertion, content, count=1)

# Add our text-shadow rules at the bottom of the file
glow_css = """

/* Dark Theme specific glow */
.theme-dark a {
  text-shadow: var(--link-glow);
}

.theme-dark h1,
.theme-dark h2,
.theme-dark h3,
.theme-dark h4,
.theme-dark h5,
.theme-dark h6 {
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}
"""

if "/* Dark Theme specific glow */" not in new_content:
    new_content += glow_css

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("CSS cleanly updated to only affect dark theme.")
