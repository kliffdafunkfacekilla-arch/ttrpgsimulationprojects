import re

names_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\names-generator.ts'
with open(names_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's just find the namebases array block
match = re.search(r'export const nameBases.*?;', content, re.DOTALL)
if match:
    bases_text = match.group(0)
    bases = re.findall(r'name:\s*\"([^\"]+)\"', bases_text)
    print(f'Total bases: {len(bases)}')
    for i, name in enumerate(bases):
        if i >= len(bases) - 25:
            print(f'{i}: {name}')
else:
    print('nameBases not found')
