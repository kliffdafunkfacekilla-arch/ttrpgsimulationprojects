import re

burgs_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\burgs-generator.ts'
with open(burgs_file, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'(const generatePrisons = \(\) => \{.*?\n    \};)', content, re.DOTALL)
if not match:
    print('Could not find generatePrisons')
    exit(1)

new_func = '''const generatePrisons = () => {
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
        "The Abyssal Prison", "Cult of the World-Ender", "The Convergence",
        "Oblivion Gate", "The Shattered Seal", "Doom's Cradle",
        "The Void Bastion", "Tether of the Beast", "The Nightmare Spire",
        "Chaos Sanctum", "The Final Lock", "Ender's Watch", "The Deep Warden"
      ];

      for (let i = 0; i < origins.length; i++) {
        const [x, y] = origins[i];
        const cell = window.findCell(x, y, undefined, pack);
        if (cell === undefined || cells.burg[cell]) continue;
        
        const burgId = burgs.length;
        burgs.push({
          cell,
          x,
          y,
          i: burgId,
          state: 0,
          culture: cells.culture[cell] || 0,
          name: i !== 2 ? prisonNames[i] + " (Dragon Cult)" : "The Convergence",
          feature: cells.f[cell],
          capital: 0,
          citadel: 1,
          walls: 1,
          plaza: 1,
          temple: 1,
          population: 10
        });
        cells.burg[cell] = burgId;

        // If it's the center (The Convergence), add The Spire next to it
        if (i === 2) {
          // Find an adjacent cell for The Spire
          const adjacentCell = cells.c[cell].find((c: number) => !cells.burg[c]);
          if (adjacentCell !== undefined) {
            const spId = burgs.length;
            const [sx, sy] = cells.p[adjacentCell];
            burgs.push({
              cell: adjacentCell,
              x: sx,
              y: sy,
              i: spId,
              state: 0,
              culture: cells.culture[adjacentCell] || 0,
              name: "The Spire (Grey Wardens)",
              feature: cells.f[adjacentCell],
              capital: 0,
              citadel: 1,
              walls: 1,
              plaza: 1,
              temple: 1,
              population: 15
            });
            cells.burg[adjacentCell] = spId;
          }
        }
      }
    };'''

content = content.replace(match.group(1), new_func)

with open(burgs_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated prisons logic successfully!')
