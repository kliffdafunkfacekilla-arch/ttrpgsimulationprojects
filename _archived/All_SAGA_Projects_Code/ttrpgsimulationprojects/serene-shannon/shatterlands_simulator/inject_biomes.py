import re

biomes_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\biomes.ts'
with open(biomes_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Add to arrays in getDefault()
content = re.sub(
    r'const name: string\[\] = \[(.*?)\];',
    lambda m: f"const name: string[] = [{m.group(1)},\n      \"Shallow Reef\",\n      \"Kelp Forest\",\n      \"Pelagic Zone\",\n      \"Abyssal Plain\",\n      \"Oceanic Trench\"\n    ];",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'const color: string\[\] = \[(.*?)\];',
    lambda m: f"const color: string[] = [{m.group(1)},\n      \"#006994\",\n      \"#004B49\",\n      \"#000080\",\n      \"#000033\",\n      \"#000011\"\n    ];",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'const habitability: number\[\] = \[(.*?)\];',
    r'const habitability: number[] = [\1, 80, 70, 30, 5, 1];',
    content
)

content = re.sub(
    r'const iconsDensity: number\[\] = \[(.*?)\];',
    r'const iconsDensity: number[] = [\1, 200, 150, 0, 0, 0];',
    content
)

content = re.sub(
    r'const icons: Array.*?= \[(.*?)\];',
    lambda m: f"const icons: Array<{{ [key: string]: number }}> = [{m.group(1)},\n      {{}},\n      {{}},\n      {{}},\n      {{}},\n      {{}}\n    ];",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'const cost: number\[\] = \[(.*?)\];',
    r'const cost: number[] = [\1, 30, 40, 200, 1000, 5000];',
    content
)

# Rewrite getId function
new_get_id = '''getId(moisture: number, temperature: number, height: number, hasRiver: boolean) {
    if (height < 20) {
      if (height >= 15) return 13; // Shallow Reef
      if (height >= 10 && temperature > 10) return 14; // Kelp Forest
      if (height >= 5) return 15; // Pelagic Zone
      if (height >= 2) return 16; // Abyssal Plain
      return 17; // Oceanic Trench
    }
    if (temperature < -5) return 11; // too cold: permafrost biome
    if (temperature >= 25 && !hasRiver && moisture < 8) return 1; // too hot and dry: hot desert biome
    if (this.isWetland(moisture, temperature, height)) return 12; // too wet: wetland biome

    // in other cases use biome matrix
    const moistureBand = Math.min((moisture / 5) | 0, 4); // [0-4]
    const temperatureBand = Math.min(Math.max(20 - temperature, 0), 25); // [0-25]
    return biomesData.biomesMatrix[moistureBand][temperatureBand];
  }'''

content = re.sub(
    r'getId\(moisture: number, temperature: number, height: number, hasRiver: boolean\) \{.*?\}',
    new_get_id,
    content,
    flags=re.DOTALL
)

with open(biomes_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Biomes injected successfully!')
