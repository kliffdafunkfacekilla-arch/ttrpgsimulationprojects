import re

biomes_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\biomes.ts'
with open(biomes_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Add to arrays in getDefault()
content = re.sub(
    r'const name: string\[\] = \[(.*?)\];',
    lambda m: f"const name: string[] = [{m.group(1)},\n      \"Chaos Land\",\n      \"Chaos Water\"\n    ];",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'const color: string\[\] = \[(.*?)\];',
    lambda m: f"const color: string[] = [{m.group(1)},\n      \"#4B0082\",\n      \"#190033\"\n    ];",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'const habitability: number\[\] = \[(.*?)\];',
    r'const habitability: number[] = [\1, 2, 2];',
    content
)

content = re.sub(
    r'const iconsDensity: number\[\] = \[(.*?)\];',
    r'const iconsDensity: number[] = [\1, 10, 0];',
    content
)

content = re.sub(
    r'const icons: Array.*?= \[(.*?)\];',
    lambda m: f"const icons: Array<{{ [key: string]: number }}> = [{m.group(1)},\n      {{ deadTree: 5 }},\n      {{}}\n    ];",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'const cost: number\[\] = \[(.*?)\];',
    r'const cost: number[] = [\1, 2000, 2000];',
    content
)

with open(biomes_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Chaos biomes injected successfully!')
