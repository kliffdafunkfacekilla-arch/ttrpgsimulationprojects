import re

biomes_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\biomes.ts'
with open(biomes_file, 'r', encoding='utf-8') as f:
    content = f.read()

chaos_func = '''
  generateChaos() {
    TIME && console.time("generateChaos");
    const { cells } = pack;
    const W = graphWidth;
    const H = graphHeight;
    
    // 13 origins
    const origins: [number, number][] = [
      [W/2, 0], // North pole
      [W/2, H], // South pole
      [W/2, H/2], // Center
    ];
    for (let i = 0; i < 5; i++) {
      origins.push([(W/5) * i, H * 0.25]); // Northern row
      origins.push([(W/5) * i + (W/10), H * 0.75]); // Southern offset row
    }

    const queue = new FlatQueue();
    const chaosLimit = Math.floor(cells.i.length * 0.1); // Chaos takes 10% of the world
    let chaosCount = 0;

    const cost = new Float32Array(cells.i.length).fill(10000);
    const isChaos = new Uint8Array(cells.i.length);
    
    for (const [x, y] of origins) {
      const cellId = window.findCell(x, y, undefined, pack);
      if (cellId !== undefined) {
        cost[cellId] = 0;
        isChaos[cellId] = 1;
        queue.push(cellId, 0);
      }
    }

    while (queue.length && chaosCount < chaosLimit) {
      const next = queue.pop();
      cells.c[next].forEach((e: number) => {
        const h = cells.h[e];
        const stepCost = h < 20 ? 10 : 20; // spreads easier in water
        const totalCost = cost[next] + stepCost;
        if (totalCost < cost[e]) {
          cost[e] = totalCost;
          isChaos[e] = 1;
          chaosCount++;
          cells.biome[e] = h < 20 ? 19 : 18; // 18 is Chaos Land, 19 is Chaos Water
          queue.push(e, totalCost);
        }
      });
    }
    TIME && console.timeEnd("generateChaos");
  }
'''

# Find the define() method end to inject the function call and the function itself.
define_end_match = re.search(r'TIME && console\.timeEnd\(\"defineBiomes\"\);\s*\}', content)
if define_end_match:
    original_end = define_end_match.group(0)
    new_end = 'this.generateChaos();\n    ' + original_end + '\n' + chaos_func
    content = content.replace(original_end, new_end)

with open(biomes_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Procedural Chaos Biomes injected successfully!')
