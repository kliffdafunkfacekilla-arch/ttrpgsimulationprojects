import re

burgs_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\burgs-generator.ts'
with open(burgs_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Task 1: Filter out Chaos from normal burg generation
old_filter = 'const populatedCells = cells.i.filter(i => cells.s[i] > 0 && cells.culture[i]);'
new_filter = 'const populatedCells = cells.i.filter(i => cells.s[i] > 0 && cells.culture[i] && cells.biome[i] !== 18 && cells.biome[i] !== 19);'
content = content.replace(old_filter, new_filter)

# Task 2: Spawn the 13 Prisons
prison_func = '''
    const generatePrisons = () => {
      const W = graphWidth;
      const H = graphHeight;
      const origins: [number, number][] = [
        [W/2, 0], [W/2, H], [W/2, H/2],
      ];
      for (let i = 0; i < 5; i++) {
        origins.push([(W/5) * i, H * 0.25]);
        origins.push([(W/5) * i + (W/10), H * 0.75]);
      }

      const prisonNames = [
        "The Abyssal Prison", "Cult of the World-Ender", "The Dark Core",
        "Oblivion Gate", "The Shattered Seal", "Doom's Cradle",
        "The Void Bastion", "Tether of the Beast", "The Nightmare Spire",
        "Chaos Sanctum", "The Final Lock", "Ender's Watch", "The Deep Warden"
      ];

      for (let i = 0; i < origins.length; i++) {
        const [x, y] = origins[i];
        const cell = window.findCell(x, y, undefined, pack);
        if (cell === undefined || cells.burg[cell]) continue; // shouldn't happen unless overlap
        
        const burgId = burgs.length;
        burgs.push({
          cell,
          x,
          y,
          i: burgId,
          state: 0, // Neutrals
          culture: cells.culture[cell] || 0,
          name: prisonNames[i],
          feature: cells.f[cell],
          capital: 0,
          citadel: 1,
          walls: 1,
          plaza: 1,
          temple: 1,
          population: 10 // small cult population
        });
        cells.burg[cell] = burgId;
      }
    };
'''

# Inject before generateCapitals();
content = content.replace('    generateCapitals();', prison_func + '\n    generatePrisons();\n    generateCapitals();')

with open(burgs_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Prisons injected successfully!')
