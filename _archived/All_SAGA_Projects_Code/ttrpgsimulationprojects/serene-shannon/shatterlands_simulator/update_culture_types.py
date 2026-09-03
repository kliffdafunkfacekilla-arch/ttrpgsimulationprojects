import re

cultures_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\cultures-generator.ts'
with open(cultures_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the fallback DEFAULT_CULTURE_TYPE with a random pick to ensure variety
old_return = 'return DEFAULT_CULTURE_TYPE;'
new_return = '''const types: CultureType[] = ["Generic", "Hunting", "Highland", "River", "Lake", "Naval", "Nomadic"];
      return rw(types);'''

content = content.replace(old_return, new_return)

with open(cultures_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated defineCultureType successfully!')
