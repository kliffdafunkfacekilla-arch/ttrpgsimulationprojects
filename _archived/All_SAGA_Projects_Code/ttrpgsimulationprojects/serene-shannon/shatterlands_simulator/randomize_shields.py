import re
import random

cultures_file = r'C:\Users\krazy\Desktop\Fantasy-Map-Generator\src\modules\cultures-generator.ts'
with open(cultures_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find the "all-world" section or the huge array returned by getDefault.
# We want to randomize the `shield: "..."` values to prevent them from being all the same.
# We also want to assign random types if there are any hardcoded types.

shields = ["heater", "round", "spanish", "square", "wedged", "banner", "oval", "pavise", "horsehead", "boeotian", "roman", "renaissance", "horsehead2", "oldFrench", "vesicaPiscis"]

def repl(match):
    return f'shield: "{random.choice(shields)}"'

content = re.sub(r'shield:\s*\"[a-zA-Z0-9_]+\"', repl, content)

with open(cultures_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('Randomized shields in cultures-generator.ts!')
