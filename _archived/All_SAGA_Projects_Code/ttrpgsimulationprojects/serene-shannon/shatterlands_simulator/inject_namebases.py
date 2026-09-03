import os
import re

ts_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\names-generator.ts'
namebases_dir = r'C:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\data\namebases'

with open(ts_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the maximum 'i:' value in the file to continue the numbering
indices = re.findall(r'i:\s*(\d+)', content)
if not indices:
    print('Error: Could not find indices')
    exit(1)
max_i = max(int(i) for i in indices)
print(f'Max index found: {max_i}')

new_objects = []
next_i = max_i + 1

for filename in os.listdir(namebases_dir):
    if filename.endswith('.txt'):
        filepath = os.path.join(namebases_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = f.read().strip()
        parts = data.split('|', 5)
        if len(parts) == 6:
            name, min_l, max_l, dup, m_rate, names = parts
            obj = f'''      {{
        name: "{name}",
        i: {next_i},
        min: {min_l},
        max: {max_l},
        d: "{dup}",
        m: {m_rate},
        b: "{names}"
      }}'''
            new_objects.append(obj)
            next_i += 1

injection_str = ',\n' + ',\n'.join(new_objects) + '\n    ];\n  }'

# Replace the end of the array
new_content = re.sub(r'(\s+\];\s+\})', injection_str, content, count=1)

with open(ts_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Successfully injected {len(new_objects)} namebases into names-generator.ts!')
