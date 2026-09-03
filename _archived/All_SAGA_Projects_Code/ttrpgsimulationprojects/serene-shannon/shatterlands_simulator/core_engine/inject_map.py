import json
import os
import shutil

src_map = r"C:\Users\krazy\Downloads\Okasha 2026-06-26-02-24.map"
bak_map = r"C:\Users\krazy\Downloads\Okasha 2026-06-26-02-24_bak.map"

shutil.copyfile(src_map, bak_map)

lore = [
    {"name": "The Whisperers", "type": "Cult", "form": "Worm Cult", "deity": "Sh'lar (The 13th Shadow)"},
    {"name": "Cult of the Crushed", "type": "Cult", "form": "Worm Cult", "deity": "Tiraton (The World-Weight)"},
    {"name": "The Frozen Heart", "type": "Cult", "form": "Worm Cult", "deity": "Stagus (Unyielding Glazier)"},
    {"name": "The Strangler Fig", "type": "Cult", "form": "Worm Cult", "deity": "Vecelo (The Silent Echo)"},
    {"name": "Toxic Liquidity", "type": "Cult", "form": "Worm Cult", "deity": "Aurgenas (Gilded Solvent)"},
    {"name": "True Smelt", "type": "Cult", "form": "Worm Cult", "deity": "Carulkem (The Furnace Eternal)"},
    {"name": "The Null-Equation", "type": "Cult", "form": "Worm Cult", "deity": "Lophex (Geometric Void)"},
    {"name": "The Blind Spot", "type": "Cult", "form": "Worm Cult", "deity": "Opecten (The Mirror Lord)"},
    {"name": "The Rotting Vessel", "type": "Cult", "form": "Worm Cult", "deity": "Termhill (The Black Star)"},
    {"name": "Quicksilver Mother", "type": "Cult", "form": "Worm Cult", "deity": "Gavusrix (Fecund Plague)"},
    {"name": "Siren Song", "type": "Cult", "form": "Worm Cult", "deity": "Virantor (The Burning Soul)"},
    {"name": "Cult of Identity", "type": "Cult", "form": "Worm Cult", "deity": "Tyrustis (The Mad King)"},
    {"name": "Mandate of the Chain", "type": "Cult", "form": "Accidental Cult", "deity": "None"},
    {"name": "Church of the Eternal Dawn", "type": "Organized", "form": "Church", "deity": "The Light"},
    {"name": "Order of Purifiers", "type": "Organized", "form": "Sect", "deity": "Purity"},
    {"name": "The Reliance", "type": "Folk", "form": "Symbiotic Faith", "deity": "The Fungal Alloy"},
    {"name": "Dust-Husk Riders", "type": "Folk", "form": "Trinity of Silence", "deity": "Silence"},
    {"name": "The Night Watch", "type": "Folk", "form": "Mythos", "deity": "Black Rider"}
]

with open(src_map, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

injected = False
for i in range(len(lines)):
    line = lines[i]
    if line.startswith('[{') and '"religions":' not in line:
        # Looking for the religions array line, which looks like [{"name":"No religion","i":0,"origins":null}...
        if '"No religion"' in line and '"origins":null' in line:
            try:
                religions = json.loads(line)
                lore_idx = 0
                for r in religions:
                    if r.get('i', 0) == 0: continue
                    if lore_idx < len(lore):
                        l = lore[lore_idx]
                        r['name'] = l['name']
                        r['type'] = l['type']
                        r['form'] = l['form']
                        r['deity'] = l['deity']
                        lore_idx += 1
                lines[i] = json.dumps(religions, separators=(',', ':'))
                injected = True
                print(f"Successfully injected {lore_idx} lore religions into the Okasha .map file.")
                break
            except json.JSONDecodeError:
                pass

if injected:
    with open(src_map, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
else:
    print("Failed to find valid religions array.")
