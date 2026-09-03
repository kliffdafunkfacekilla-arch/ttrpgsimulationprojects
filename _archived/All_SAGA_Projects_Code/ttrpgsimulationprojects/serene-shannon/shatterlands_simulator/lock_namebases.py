import re

cultures_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\cultures-generator.ts'
with open(cultures_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's completely replace the "all-world" fallback in getDefault()
# with logic that takes the last 20 namebases (which are the user's custom ones).
# Currently the end of getDefault is something like:
#     // all-world
#     return [
#       {
#         name: "Shwazen",

# I will find `// all-world` and replace the rest of the method until the closing brace of getDefault()
match = re.search(r'// all-world.*?return \[.*?\];\s*\}', content, re.DOTALL)
if match:
    new_code = '''// all-world - LOCKED TO CUSTOM LORE FACTIONS
    return Array.from({ length: 20 }, (_, i) => {
      // nameBases.length is the total, we want the last 20
      const baseIndex = nameBases.length - 20 + i;
      const name = Names.getBaseShort(baseIndex);
      return {
        name,
        base: baseIndex,
        odd: 1,
        shield: this.getRandomShield() // Randomize shields as requested!
      };
    });
  }'''
    content = content.replace(match.group(0), new_code)
    
    with open(cultures_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Locked in custom namebases to all-world generator!')
else:
    print('all-world block not found')
