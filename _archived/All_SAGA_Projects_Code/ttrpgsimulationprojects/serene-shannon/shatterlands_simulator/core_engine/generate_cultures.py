import os
import csv
import random

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cultures.csv")

# Map of species to their Kingdom (Type) and a fitting Namebase
SPECIES_MAP = {
    "Mammals": [
        ("Ursine", "Ursine"),
        ("Canid-Kin", "Eastern Hounds"),
        ("Equines", "Heartland"),
        ("Grazer-Kin", "Heartland"),
        ("Beavers", "Riverfolk"),
        ("Raccoons", "Dusk Husk"),
        ("Small-Paws", "Dusk Husk"),
        ("Canopy-Climbers", "Canopy"),
        ("Ailurus", "Canopy"),
        ("Quill-Kin", "Guirilla Clans"),
        ("Wolverines", "Ursine"),
        ("Manis", "Iron Caladra")
    ],
    "Reptiles": [
        ("Stone-Scales", "Scute"),
        ("Monitor-Kin", "Scute"),
        ("Geckos", "Devils Island"),
        ("Pit-Vipers", "Devils Island"),
        ("Gliding Skinks", "Prism"),
        ("Frilled-Lizards", "Prism"),
        ("Shovel-Snouts", "Vaneer"),
        ("Serpent-Kin", "Devils Island"),
        ("Crocodilians", "Riverfolk"),
        ("Toads", "Sumpkin"),
        ("Newts", "Sumpkin"),
        ("Frogs", "Sumpkin")
    ],
    "Plants": [
        ("Cacti", "Vaneer"),
        ("Drifters", "Sylvian"),
        ("Sylvan Ancients", "Sylvian"),
        ("Iron-Woods", "Iron Caladra"),
        ("Weeping Mangroves", "Sumpkin"),
        ("Moon-Blossoms", "Flower Valley"),
        ("Sun-Blossoms", "Flower Valley"),
        ("Corpse-Lilies", "Dusk Husk"),
        ("Iron-Brambles", "Iron Caladra"),
        ("Berry-Bushes", "Flower Valley"),
        ("Vines", "Sylvian"),
        ("Reliance", "Relieance")
    ],
    "Aquatics": [
        ("Dolphin-Kin", "Riverfolk"),
        ("Walrus-Kin", "Ursine"),
        ("Elephant Seals", "Ursine"),
        ("Orcas", "Riverfolk"),
        ("Catfish", "Sumpkin"),
        ("Otters", "Riverfolk"),
        ("Shark-Kin", "Devils Island"),
        ("Crustacean-Kin", "Scute"),
        ("Seahorses", "Prism"),
        ("Moray-Kin", "Riverfolk"),
        ("Gar-Pikes", "Riverfolk"),
        ("Salmon-Kin", "Riverfolk")
    ],
    "Insects": [
        ("Widow Spiders", "Hive Collective"),
        ("Ant-Kin", "Hive Collective"),
        ("Mantises", "Hive Collective"),
        ("Scorpions", "Vaneer"),
        ("Beetles", "Iron Caladra"),
        ("Stinging Hive-Kin", "Hive Collective"),
        ("Silk Worms", "Meridian Chain"),
        ("Roach-Kin", "Dusk Husk"),
        ("Moths", "Canopy"),
        ("Ladybugs", "Flower Valley"),
        ("Dragonflies", "Prism"),
        ("Flies", "Hive Collective")
    ],
    "Avians": [
        ("Eagles", "Avian"),
        ("Falcons", "Avian"),
        ("Owls", "Theocracy"),
        ("Crows", "Dusk Husk"),
        ("Jays", "Canopy"),
        ("Vultures", "Vaneer"),
        ("Sparrows", "Heartland"),
        ("Cardinals", "Theocracy"),
        ("Thrushes", "Sylvian"),
        ("Terror-Fowl", "Guirilla Clans"),
        ("Fowl", "Heartland"),
        ("Penguins", "Riverfolk")
    ]
}

def random_color_for_kingdom(kingdom):
    if kingdom == "Mammals": # Browns/Reds
        return "#{:02x}{:02x}{:02x}".format(random.randint(100, 200), random.randint(50, 100), random.randint(20, 60))
    elif kingdom == "Reptiles": # Dark Greens/Browns
        return "#{:02x}{:02x}{:02x}".format(random.randint(30, 100), random.randint(100, 180), random.randint(30, 80))
    elif kingdom == "Plants": # Bright Greens
        return "#{:02x}{:02x}{:02x}".format(random.randint(50, 120), random.randint(150, 220), random.randint(50, 100))
    elif kingdom == "Aquatics": # Blues/Teals
        return "#{:02x}{:02x}{:02x}".format(random.randint(20, 80), random.randint(100, 180), random.randint(180, 240))
    elif kingdom == "Insects": # Purples/Yellows
        if random.random() > 0.5:
            return "#{:02x}{:02x}{:02x}".format(random.randint(120, 200), random.randint(30, 80), random.randint(150, 220))
        return "#{:02x}{:02x}{:02x}".format(random.randint(180, 240), random.randint(180, 220), random.randint(20, 60))
    else: # Avians - Whites/Light Blues
        return "#{:02x}{:02x}{:02x}".format(random.randint(180, 240), random.randint(200, 255), random.randint(200, 255))

def main():
    with open(OUT_PATH, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Color", "Type", "Expansionism", "Base"])
        
        for kingdom, species_list in SPECIES_MAP.items():
            for species, namebase in species_list:
                color = random_color_for_kingdom(kingdom)
                writer.writerow([species, color, kingdom, "1.0", namebase])
                
    print(f"Generated 72 cultures and saved to {OUT_PATH}")

if __name__ == "__main__":
    main()
