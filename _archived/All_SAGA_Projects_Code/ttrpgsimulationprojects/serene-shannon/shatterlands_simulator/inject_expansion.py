import re

cultures_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\cultures-generator.ts'
with open(cultures_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace populationCost in expand()
old_pop = "const populationCost = cells.h[e] < 20 ? 0 : cells.s[e] ? Math.max(20 - cells.s[e], 0) : 5000;"
new_pop = "const populationCost = cells.h[e] < 20 && !pack.cultures[c].isAquatic ? 0 : cells.s[e] ? Math.max(20 - cells.s[e], 0) : 5000;"
content = content.replace(old_pop, new_pop)

# In expand(), change assigning state to cell:
old_assign = "if (cells.h[e] >= 20) cells.culture[e] = c; // assign culture to cell"
new_assign = "if (cells.h[e] >= 20 || pack.cultures[c].isAquatic) cells.culture[e] = c; // assign culture to cell"
content = content.replace(old_assign, new_assign)

# In normalize():
old_norm = "if (cells.h[i] < 20) continue; // do not overwrite water"
new_norm = "if (cells.h[i] < 20 && !pack.cultures[cells.culture[i]]?.isAquatic) continue; // do not overwrite water"
content = content.replace(old_norm, new_norm)

with open(cultures_file, 'w', encoding='utf-8') as f:
    f.write(content)

states_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\states-generator.ts'
with open(states_file, 'r', encoding='utf-8') as f:
    content = f.read()

# In expandStates():
old_pop2 = "const populationCost = cells.h[e] < 20 ? 0 : cells.s[e] ? Math.max(20 - cells.s[e], 0) : 5000;"
new_pop2 = "const populationCost = cells.h[e] < 20 && !states[s].isAquatic ? 0 : cells.s[e] ? Math.max(20 - cells.s[e], 0) : 5000;"
content = content.replace(old_pop2, new_pop2)

old_assign2 = "if (cells.h[e] >= 20) cells.state[e] = s; // assign state to cell"
new_assign2 = "if (cells.h[e] >= 20 || states[s].isAquatic) cells.state[e] = s; // assign state to cell"
content = content.replace(old_assign2, new_assign2)

old_norm2 = "if (cells.h[i] < 20 || cells.burg[i]) continue; // do not overwrite burgs"
new_norm2 = "if ((cells.h[i] < 20 && !pack.states[cells.state[i]]?.isAquatic) || cells.burg[i]) continue; // do not overwrite burgs"
content = content.replace(old_norm2, new_norm2)

with open(states_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Expansion logic updated!')
