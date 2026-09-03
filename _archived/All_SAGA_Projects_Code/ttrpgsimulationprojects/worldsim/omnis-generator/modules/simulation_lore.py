# simulation_lore.py
# This file contains python-native structures of Ostraka lore elements for simulation import

FACTIONS = [
    # === Main Factions (17) ===
    {
        "name": "Ursine Hegemony",
        "base_of_operations": "Snowpeak Citadel (The Great Hearth)",
        "key_leaders": "Great Hearth-Mother and Clan Chieftains",
        "description": "A highly disciplined, defensive union of Ursine clans who protect travelers and maintain the Great Hearth. Outwardly warm, hospitable, and jovial, they are unyielding under external pressure.",
        "mechanics": "Enforce the Sigil of Ice to create localized zones of absolute thermal stillness, neutralizing flame-based and chaotic heat hazards.",
        "special_sight_protocol": None
    },
    {
        "name": "River Folk",
        "base_of_operations": "Opal-Delta & Bathhouses",
        "key_leaders": "The Delta Council and Guildmasters",
        "description": "An agile society of waterway specialists, swimmers, fishers, and merchants. They manage trade, shipping, and navigation channels across Ostraka's rivers and lakes.",
        "mechanics": "Attuned to aquatic currents; their vessels ignore speed penalties during seasonal floods.",
        "special_sight_protocol": None
    },
    {
        "name": "Sump-Kin",
        "base_of_operations": "Port Sunder Silt-docks & Cavern Swamps",
        "key_leaders": "Toad Barons and Chem-Barons",
        "description": "Industrialists running heavy refining, chemical processing, and toxic waste management. Attuned to hazardous environments.",
        "mechanics": "High-molarity toxin immunity, enabling safe transit and resource extraction in heavily poisoned or acid-ridden areas.",
        "special_sight_protocol": None
    },
    {
        "name": "Iron Caladrea",
        "base_of_operations": "The Iron Caldera & Anvil Spire",
        "key_leaders": "High Forgemaster and Smith Guilds",
        "description": "Industrial giants, smiths, and engineers of Ostraka. They quarry deep veins, operate high-temperature blast furnaces, and manufacture heavy alloys.",
        "mechanics": "Access to high-tier iron smelting and refractory technology, allowing construction of durable structures like stone and metal outposts.",
        "special_sight_protocol": None
    },
    {
        "name": "Vaneer Concord",
        "base_of_operations": "Secure Burrows & Auditing Centers",
        "key_leaders": "Logistical Auditors and High Scribes",
        "description": "A highly bureaucratic, detail-oriented state. They weaponize administrative audits and supply logistics to maintain political control.",
        "mechanics": "Utilize hyper-efficient bookkeeping to detect resources and bypass trade blockades.",
        "special_sight_protocol": None
    },
    {
        "name": "Hive Collective",
        "base_of_operations": "The Honeycomb Citadels",
        "key_leaders": "Queen Sovereign and Hive Mind Elders",
        "description": "A highly organized, collective society linked by a shared Hive Mind. Attuned to rapid production, construction, and agriculture.",
        "mechanics": "Share intelligence and coordinates instantaneously across all units in regional sectors, making surprise attacks ineffective.",
        "special_sight_protocol": None
    },
    {
        "name": "Avians",
        "base_of_operations": "Excelsis Citadel (The Vertical Capital)",
        "key_leaders": "The High Judge and Council of Notaries",
        "description": "The administrative, legal, and judicial authority of Ostraka. Feathered bird-kin who physically cannot tell a direct lie.",
        "mechanics": "Utilize the amber-preserved eye of Emperor Kaelos to detect falsehoods and enforce Shadow-Set contracts that physically bind signatories.",
        "special_sight_protocol": None
    },
    {
        "name": "Flower Valwey",
        "base_of_operations": "Lush Meadows & Alchemical Gardens",
        "key_leaders": "Floral Keepers and Botanical Druids",
        "description": "A lush agricultural and botanical hub. They specialize in growing rare plants, distilling essences, and practicing alchemical medicine.",
        "mechanics": "Cultivate rare medical crops like Ghost Flowers and Night-Nectar, which cure static rot and boost navigation foresight.",
        "special_sight_protocol": None
    },
    {
        "name": "Sylvian",
        "base_of_operations": "Arbor-Prime (The Walking City)",
        "key_leaders": "Forest Shamans and Tree-Kin Elders",
        "description": "Woodland guardians who live in harmony with Ostraka's ancient forests. Their capital is Arbor-Prime, a colossal walking city built on the backs of ancient wooden structures.",
        "mechanics": "Able to manipulate plant growth and navigate dense forests with zero movement penalty.",
        "special_sight_protocol": None
    },
    {
        "name": "Sciute",
        "base_of_operations": "Coastal Shelves & Stone Towers",
        "key_leaders": "The Stonemason Council",
        "description": "A stable society of stonemasons, builders, and turtle-kin who value structural preservation and physical endurance.",
        "mechanics": "Can construct highly defensive stone and brick fortifications that resist seismic and gravity fluctuations.",
        "special_sight_protocol": None
    },
    {
        "name": "Meridian Chain",
        "base_of_operations": "Bridge-Cities and the Blue-Route",
        "key_leaders": "The Snail-Lords and Wick-Keeper Council",
        "description": "A commercial hexarchy that operates maritime trade routes. They run Snail-Draught logistics using house-sized Abyssal Snails dragging heavy iron barges.",
        "mechanics": "Deploy low-frequency Depth-Chimes to coordinate shipping through turbid waters.",
        "special_sight_protocol": None
    },
    {
        "name": "Prism Lizards",
        "base_of_operations": "Lumen-Spire (The Glass City)",
        "key_leaders": "Mirror Lords and Light Weaver Council",
        "description": "An advanced collective that manipulates light and reflections. They build crystalline cities with complex reflector networks.",
        "mechanics": "Deploy Chromium-based mirrors to project light beams, amplify surveillance, and detect cloaked entities.",
        "special_sight_protocol": None
    },
    {
        "name": "Canopy Clans",
        "base_of_operations": "High-Altitude Forest Roosts",
        "key_leaders": "Chieftains of the Wind-Wake",
        "description": "A high-altitude society of canopy-dwellers. They reside in high-tier branches, harvesting wind currents and sky-grazer products.",
        "mechanics": "Attuned to high-altitude navigation; immune to static electrical hazards in storm zones.",
        "special_sight_protocol": None
    },
    {
        "name": "East Hounds",
        "base_of_operations": "Howling Steppes",
        "key_leaders": "Shamanic Chieftains",
        "description": "Nomadic steppe-kin and wolves who roam the volatile wind plains, communicating with the spirits of the past.",
        "mechanics": "Enforce pack-hunting tactics; shamans can read temporal echoes to locate lost trails.",
        "special_sight_protocol": None
    },
    {
        "name": "Guirrilla Clans",
        "base_of_operations": "Grind Canyon Crevices & Rift Caves",
        "key_leaders": "Rift Captains",
        "description": "Rebellious survivalist clans who hide in the geological fractures of the Grind Canyons, executing rapid ambushes.",
        "mechanics": "Utilize canyon terrain to mask movement, bypassing standard radar and scouts.",
        "special_sight_protocol": None
    },
    {
        "name": "Theocracy",
        "base_of_operations": "Sovereign Coral Temples & Trench Citadels",
        "key_leaders": "High Priesthood of the Deep",
        "description": "A religious society of aquatic kin (whales, dolphins) chemically addicted to the frequency of Virantor. They build custom airships to reclaim land for the sea.",
        "mechanics": "Ignite Phosphorus Spirit-Fires, converting psychic energy into raw flame and panic.",
        "special_sight_protocol": None
    },
    {
        "name": "The Reliance",
        "base_of_operations": "Subterranean Caverns & Scholar Prisons",
        "key_leaders": "Mushroom-Kin Elders",
        "description": "Fungal scholars acting as neutral keepers of Ostraka's dangerous data. They guard stasis cages holding Class-IV hazards and store records.",
        "mechanics": "Secretes Chaos-Immune Fungal Alloy, requiring the total systematic erasure of a candidate's memory.",
        "special_sight_protocol": None
    },

    # === Fringe Groups (9) ===
    {
        "name": "Obsidian Cartel and Sister Org",
        "base_of_operations": "The Underworld Vaults",
        "key_leaders": "The Shadow Council",
        "description": "The primary 'Shadow-Engine' of Ostraka. Partnered with the Silk-Sovereign Syndicate, they broker illegal assets, manage stasis-banking, and maintain underworld parity.",
        "mechanics": "Utilize Silk-Steel cables and Bismuth-lined passages to bypass surveillance and arcane barriers.",
        "special_sight_protocol": None
    },
    {
        "name": "Freesky Barons",
        "base_of_operations": "Floating Skiffs & Sky Wakes",
        "key_leaders": "Sovereign Barons of the Cloud-Wake",
        "description": "Independent aeronauts and anti-chaos anarchists. They fly into volatile zones to mine Dragonstone and smuggle vital supplies.",
        "mechanics": "Deploy Jitter-Rigs to chart real-time shifts in high-chaos zones, avoiding rifts.",
        "special_sight_protocol": None
    },
    {
        "name": "Ghost Wind Raiders",
        "base_of_operations": "High-Altitude Silt Currents",
        "key_leaders": "Smuggling Captains",
        "description": "Clandestine sky pirates funded secretly by the Meridian Chain to conduct black ops and asset denial.",
        "mechanics": "Utilize silt-strata reversals to mask their signatures from Avian high-altitude sensors.",
        "special_sight_protocol": None
    },
    {
        "name": "Gilded Compass",
        "base_of_operations": "Port Sunder High-Roosts & Trade Lanes",
        "key_leaders": "Cartographic Directors",
        "description": "A high-power financial and cartographical syndicate controlling trade maps and banking.",
        "mechanics": "Draft trade agreements with technical omissions to bypass the Avian inability to lie.",
        "special_sight_protocol": None
    },
    {
        "name": "Crimson Coursairs",
        "base_of_operations": "Aetheric Backwash Bays",
        "key_leaders": "Catfish Captains",
        "description": "Smuggler fleets who navigate high-velocity energy reversals. They serve as a check on economic monopolies.",
        "mechanics": "Can dive into volatile aetheric backwash to break tracking and escape pursuing authorities.",
        "special_sight_protocol": None
    },
    {
        "name": "Silent Current",
        "base_of_operations": "Deep Ocean Trenches",
        "key_leaders": "Trench Lords",
        "description": "A secretive marine syndicate operating under the surface. They run smuggling tracks through the deepest rifts.",
        "mechanics": "Unstable water navigation; vessels remain undetected by surface lookouts.",
        "special_sight_protocol": None
    },
    {
        "name": "The Black Label",
        "base_of_operations": "No-Man's-Land Outposts",
        "key_leaders": "Captain Commander",
        "description": "An elite independent mercenary guild dealing in dangerous cargo and VIP protection.",
        "mechanics": "Deploy specialized heavy enforcers (Wolverines) who physically block hazards from entering secure zones.",
        "special_sight_protocol": None
    },
    {
        "name": "The Otter Syndicate",
        "base_of_operations": "Heartland River Networks",
        "key_leaders": "Krewe Leaders",
        "description": "Riverine smugglers and black market krewes operating in canals and under city bridges.",
        "mechanics": "Move cargo silently through sewers and waterways, ignoring local tolls and tax gates.",
        "special_sight_protocol": None
    },
    {
        "name": "The Spring Ghosts",
        "base_of_operations": "Volatile Mistlands",
        "key_leaders": "The Whispering Shade",
        "description": "Spies and assassins who emerge during high-static weather phases to execute political sabotage.",
        "mechanics": "High-static phase invisibility; they leave zero trace during Shadow Week.",
        "special_sight_protocol": None
    },

    # === Wardens and Cults (2) ===
    {
        "name": "The Grey Wardens",
        "base_of_operations": "The Sacred Spire (Head and torso of dead Engineer God)",
        "key_leaders": "The Circle of the Eyeless",
        "description": "The ultimate guardians of Ostraka, originally founded by the twelve Traitor Captains. They maintain the Tensegrity grid and guard the Dragonstone prisons.",
        "mechanics": "Sew sigil-threads into flesh to channel raw chaos at the cost of physical decay; perform stabilizing kamikaze detonations.",
        "special_sight_protocol": "Chaos Sight: Blindness allows perfect perception of Ley-line fractures."
    },
    {
        "name": "The 13 Chaos Cults",
        "base_of_operations": "Shadow Cells & Infiltrated Centers",
        "key_leaders": "Sh'lar (Prime Corruptor / 13th Shadow) and Cult leaders",
        "description": "Decentralized networks of religious fanatics and political saboteurs seeking to release the Chaos Dragons.",
        "mechanics": "Weaponize specific elemental transmutations and logic-rot to trigger catastrophic blowouts in major infrastructure.",
        "special_sight_protocol": None
    }
]

SPECIES = [
    {
        "name": "Beavers",
        "homeland": "Heartland Alliance (Valerius Wall, Canal Locks)",
        "traits": "Constructors and geomancers of infrastructure. Reinforced iron-deposit teeth, flat trowel tails to send Geotremors.",
        "societal_function": "Builders, architects, and riverine specialists managing dams, sewers, and aquifers."
    },
    {
        "name": "Hippos",
        "homeland": "Opal-Delta (Great Lake and bathhouses)",
        "traits": "Deceptively strong biological siege engines with high EQ. Able to read unspoken intent and micro-expressions.",
        "societal_function": "Bank managers, heavy security guards, and translators of intent for Gilded Compass Cartel."
    },
    {
        "name": "Owls",
        "homeland": "Excelsis Citadel and Roosts of Port Sunder",
        "traits": "Feathered bird-kin who cannot tell a direct lie. Hyper-logical and truth-bound.",
        "societal_function": "Administrative judges, high executors, and contract notaries."
    },
    {
        "name": "Horses",
        "homeland": "Heartland Alliance (Oakhaven Estates)",
        "traits": "Noble and knightly, view themselves as natural guardians of the earth. Enforce Warning Systems.",
        "societal_function": "Aristocrats, politicians, and land managers who fund infrastructure."
    },
    {
        "name": "Wolves",
        "homeland": "Heartland Alliance",
        "traits": "Fierce canine pack fighters with excellent defensive instincts.",
        "societal_function": "Militia officers, soldiers, and border guards."
    },
    {
        "name": "Bears",
        "homeland": "Shifting Delta (Vortex Taverns)",
        "traits": "Imposing Ursine who have abandoned tribal homes to protect travelers. Enforce the Sigil of Ice.",
        "societal_function": "Innkeepers, bouncers, and safety escorts."
    },
    {
        "name": "Sloths",
        "homeland": "Peculiurus Spire (Fulcrum Bank)",
        "traits": "Bradypods with slow metabolic rates, immune to panic and fear. Ranch giant Weaver-Cows.",
        "societal_function": "Bankers, keepers of stasis vaults, and silk-steel cable producers."
    },
    {
        "name": "Toads",
        "homeland": "Port Sunder Silt-docks and Sump-Kin wetlands",
        "traits": "Amphibians resistant to chemical sludge, heavy metals, and toxic waste.",
        "societal_function": "Industrialists, refinery chem-barons, and waste supervisors."
    },
    {
        "name": "Mice",
        "homeland": "Vaneer Concord secure burrows",
        "traits": "Small-paws with hyper-efficient clerical processing, weaponizing data-management and audits.",
        "societal_function": "Logistical auditors, bookkeeping clerks, and supply regulators."
    },
    {
        "name": "Bats",
        "homeland": "Heartland night watch",
        "traits": "Nocturnal sentinels with acute hearing and long-distance sonic screech signaling.",
        "societal_function": "Scouts, security sentinels, and early-warning lookouts."
    },
    {
        "name": "Porcupines",
        "homeland": "Heartland Alliance alchemical centers",
        "traits": "Quill-kin using molted quills as single-use scalpels sharper than steel.",
        "societal_function": "Specialized doctors, surgeons, and alchemists."
    },
    {
        "name": "Otters",
        "homeland": "Heartland rivers and Port Sunder docks",
        "traits": "Riverine specialists and agile swimmers who run the black market and smuggling krewes.",
        "societal_function": "Convoys, shipping navigators, and black market smugglers."
    },
    {
        "name": "Deer",
        "homeland": "Heartland farmlands",
        "traits": "Horned commons farming class, capable of harvesting edges of storm fronts.",
        "societal_function": "Agrarian producers, growers, and food providers."
    },
    {
        "name": "Mongooses",
        "homeland": "Shifting Delta and elite merchant caravans",
        "traits": "Mungo bodyguards with hyper-fast twitch muscle reflexes capable of preempting Flux-Shifts.",
        "societal_function": "Elite bodyguards, anti-ambush specialists, and scouts."
    },
    {
        "name": "Cactus-Kin",
        "homeland": "The Dust Bowl",
        "traits": "Symbiotic plant succulants (Saguaro, Yucca) with spine hides who act as ballast.",
        "societal_function": "Smuggling skiff ballast, moisture storage protectors."
    },
    {
        "name": "Mushroom-Kin",
        "homeland": "Subterranean cavern systems",
        "traits": "Fungal hive-memory humanoids immune to direct chaos-bleed.",
        "societal_function": "Database archivists, creators of fungal alloy metals, and stasis cell wardens."
    }
]

RESOURCES = [
    # --- Unique Ostraka Resources ---
    {
        "name": "Dragonstone",
        "origin": "Mined from continental friction rifts and tectonic tear zones",
        "physical_properties": "Crystalline geological structures capable of absorbing and storing volatile Chaos energy.",
        "applications": "Refined into Aether-Tech batteries for ships, heating systems, and mechanical automation. Also used to construct the elemental containment vessels for the Chaos Dragons."
    },
    {
        "name": "Voltaic Fleece",
        "origin": "Shorn from Sky-Grazers floating in the Northern Outer Cliffs",
        "physical_properties": "Keratin-like strands containing a conductive gel that glows with St. Elmo's Fire when fully charged.",
        "applications": "Functions as the world's finest static electrical and reality-decay insulator once drained of its charge. Used to manufacture protective suits (PPE) for Aether-Tech engineers."
    },
    {
        "name": "Ozone-Milk",
        "origin": "Harvested as a metabolic byproduct from Sky-Grazers",
        "physical_properties": "Extremely volatile, high-energy fluid.",
        "applications": "Stabilized with titanium coolants and used to fuel high-altitude furnaces, machinery, and the communal 'Spark-Bread' for festival rituals."
    },
    {
        "name": "Fungal Alloy",
        "origin": "Secreted during the 'Ritual of Sporing' by Mushroom-kin in the Reliance vaults",
        "physical_properties": "Organic, memory-infused metal that is completely immune to reality-warping and chaos-rotation shifts.",
        "applications": "Used to write Master Ledgers, construct high-security scholar cages, and shield sensitive data."
    },
    {
        "name": "Ghost Flower",
        "origin": "Harvested from the high-static zones of the Dust Bowl",
        "physical_properties": "Volatile desert blossom that decays into useless mineral dust if dry.",
        "applications": "Refined into 'Aether-Clear' medicine to treat mental static and used in elite 'Void-Cream' cosmetics."
    },
    {
        "name": "Night-Nectar",
        "origin": "Harvested from Moon-Flowers in the deep forests",
        "physical_properties": "Grants heightened sensory foresight.",
        "applications": "Consumed by navigators to foresee upcoming storm shifts and avoid Aetheric rifts."
    },
    {
        "name": "D-Dust (Dragonstone Dust)",
        "origin": "Residue from cutting and refining Dragonstone crystals",
        "physical_properties": "Magically reactive, fine powder.",
        "applications": "Mixed with ink for the Shadow-Set ritual, binding contract terms directly to the flesh of the signatories."
    },
    {
        "name": "Salt",
        "origin": "Evaporated from the coastal margins and deep dry beds",
        "physical_properties": "Crystalline mineral acting as a holy ward and physical desiccant.",
        "applications": "Required by legal mandate to line all quarters and storage vessels to repel 'The Dry Rot' (desiccation)."
    },

    # --- Standard Stock Resources ---
    {
        "name": "Lumber",
        "origin": "Felled from standard oak and spruce woodlands",
        "physical_properties": "Solid, cut timber blocks.",
        "applications": "Essential for general construction, firewood, basic fortifications, and boat frames."
    },
    {
        "name": "Iron Ore",
        "origin": "Quarried from basic surface veins and shallow mines",
        "physical_properties": "Raw, heavy magnetic rock containing high concentrations of iron.",
        "applications": "Smelted down to forge standard tools, standard steel alloys, and weapons."
    },
    {
        "name": "Stone",
        "origin": "Excavated from granite and slate quarries",
        "physical_properties": "Dense, heavy mineral blocks.",
        "applications": "Building solid structures, stone bridges, foundations, and roads."
    },
    {
        "name": "Copper Ore",
        "origin": "Mined from subterranean deposits",
        "physical_properties": "Greenish-brown mineral veins containing soft conductive metal.",
        "applications": "Alloyed with tin for bronze or used for basic electrical grounding wires."
    },
    {
        "name": "Coal",
        "origin": "Mined from deep geological layers",
        "physical_properties": "Combustible black sediment rock.",
        "applications": "Standard fuel source for smelters, home heating, and standard steam engines."
    },
    {
        "name": "Grain",
        "origin": "Harvested from farming plains (wheat and rye)",
        "physical_properties": "Dry, organic seed crop.",
        "applications": "Processed into flour for bread, animal feed, and brewing alcohol."
    },
    {
        "name": "Leather",
        "origin": "Sourced from standard livestock like deer and bison",
        "physical_properties": "Flexible, tough cured hide.",
        "applications": "Saddles, straps, basic armor, boots, and bellows for blacksmithing."
    }
]

PRODUCED_ITEMS = [
    # ==================== TIER 1: INTERMEDIATE & REFINE GOODS ====================
    {
        "name": "Flour",
        "tier": 1,
        "composition": "Ground Grain resource processed in windmills or watermills.",
        "purpose": "Primary culinary foundation used to bake complex travel rations.",
        "user_mechanics": "Prolonged storage lifespan compared to raw grains."
    },
    {
        "name": "Peak-Cheese",
        "tier": 1,
        "composition": "Stabilized Ozone-Milk mixed with high-altitude salts and alpine cultures.",
        "purpose": "A dense, rich foodstuff that does not decay under temperature spikes.",
        "user_mechanics": "Provides high energy for summit travelers; traded heavily by River Folk."
    },
    {
        "name": "Smelted Steel",
        "tier": 1,
        "composition": "Refined Iron Ore processed in high-temperature blast furnaces fueled by Coal.",
        "purpose": "High-durability metal ingots.",
        "user_mechanics": "The metallurgical substrate for all advanced weapons and machinery."
    },
    {
        "name": "Copper Wire",
        "tier": 1,
        "composition": "Drawn Copper Ore refined into flexible strands.",
        "purpose": "Conductive threads for grounding and minor clockwork systems.",
        "user_mechanics": "Used to channel energy pathways and construct shock-dispersal items."
    },
    {
        "name": "Refined Aether Battery",
        "tier": 1,
        "composition": "Raw Dragonstone crystal shards encased in lead-alloy frames and charged with static energy.",
        "purpose": "Channeled power source for Aether-Tech machinery.",
        "user_mechanics": "The core battery that drives engines and navigation instruments."
    },
    {
        "name": "Shadow-Set Ink",
        "tier": 1,
        "composition": "Natural plant dyes mixed with fine D-Dust and processed under specific moon phases.",
        "purpose": "Active binding ink used by Notaries.",
        "user_mechanics": "Reacts to intent when tattooed onto skin during agreement rituals."
    },
    {
        "name": "Drained Fleece Wool",
        "tier": 1,
        "composition": "Raw Voltaic Fleece shorn with ceramic blades and slowly discharged in copper wells.",
        "purpose": "Insulative, reality-decay proof fiber.",
        "user_mechanics": "Safe to spin and handle by standard workers without sparking explosive blowouts."
    },
    {
        "name": "Silk-Steel Thread",
        "tier": 1,
        "composition": "Weaver-Cow silk harvested by Bradypods and spun with fine steel fibers.",
        "purpose": "A high-tension intermediate thread.",
        "user_mechanics": "Stronger than hemp or standard iron wire; used to weave heavy cables."
    },
    {
        "name": "Tanned Strips",
        "tier": 1,
        "composition": "Cured Leather treated with acidic wood tannin and salt.",
        "purpose": "Reinforced strap material.",
        "user_mechanics": "Highly resistant to wear, torque, and tearing."
    },

    # ==================== TIER 2: FINISHED & ADVANCED PRODUCTS ====================
    {
        "name": "Ostrakan Hardtack",
        "tier": 2,
        "composition": "Baked mixture of Flour, salt, and water.",
        "purpose": "An indestructible, long-lasting ration block for caravaneers.",
        "user_mechanics": "Virtually immune to standard rot and dampness; requires soaking in tea to consume."
    },
    {
        "name": "Caldera Spark-Bread",
        "tier": 2,
        "composition": "Peak-Cheese baked with Flour and stabilized Ozone-Milk.",
        "purpose": "Energetic food consumed during community rituals and high-labor projects.",
        "user_mechanics": "Temporarily restores stamina and increases thermal tolerance for miners."
    },
    {
        "name": "Iron Tools",
        "tier": 2,
        "composition": "Smelted Steel blades fitted to shaped Lumber shafts.",
        "purpose": "High-durability axes, pickaxes, and shovels.",
        "user_mechanics": "Improves mineral mining and forestry resource extraction yields."
    },
    {
        "name": "Basic Weapons",
        "tier": 2,
        "composition": "Smelted Steel blades, Lumber handles, and Tanned Strips grips.",
        "purpose": "Swords, spears, and recurve bows for militia use.",
        "user_mechanics": "Allows defense against wild beast packs and improves hunting efficacy."
    },
    {
        "name": "Grounding Chains",
        "tier": 2,
        "composition": "Copper Wire links woven into thick chains and plated with elemental Bismuth.",
        "purpose": "Arcane energy grounding harnesses worn by Null monks.",
        "user_mechanics": "Disperses surrounding magical anomalies and charges local Sacred Grove batteries."
    },
    {
        "name": "Aether-Skiff",
        "tier": 2,
        "composition": "Lumber hull, Silk-Steel Thread rigging, and two Refined Aether Batteries.",
        "purpose": "High-altitude transport vessel.",
        "user_mechanics": "Allows travel across floating continental fragments and atmospheric zones."
    },
    {
        "name": "Jitter-Rig",
        "composition": "Refined Aether Battery connected to Copper Wire coils and tuning forks.",
        "tier": 2,
        "purpose": "Navigational compass reading chaos frequencies.",
        "user_mechanics": "Vibrates and rings in different pitch keys to warn of tectonic shifts."
    },
    {
        "name": "Shadow-Seal Contract",
        "tier": 2,
        "composition": "Paper or vellum documents inscribed with Shadow-Set Ink and tattooed to skin.",
        "purpose": "Absolute legal agreement enforcement.",
        "user_mechanics": "Breaches result in permanent physical black scarring and tissue desiccation."
    },
    {
        "name": "Aether-Wright PPE",
        "tier": 2,
        "composition": "Suits woven from Drained Fleece Wool and stitched with Silk-Steel Thread.",
        "purpose": "Hazardous environment suits for engineers.",
        "user_mechanics": "Protects against gravity fluctuations and reality storms during blowouts."
    },
    {
        "name": "Silk-Steel Cables",
        "tier": 2,
        "composition": "Multiple strands of Silk-Steel Thread twisted into massive ropes.",
        "purpose": "High-tension suspension lines.",
        "user_mechanics": "Anchors floating islands and supports bridge-city infrastructure."
    },
    {
        "name": "Leather Armor",
        "tier": 2,
        "composition": "Tanned Strips stitched onto a thick linen backing with copper rivets.",
        "purpose": "Standard physical protection.",
        "user_mechanics": "Reduces physical damage from beast claws and falling shale."
    },
    {
        "name": "Rope",
        "tier": 2,
        "composition": "Woven plant fibers (hemp or fern stalks).",
        "purpose": "General cargo tie-downs and building hoisting.",
        "user_mechanics": "Standard low-cost utility tool used across all docks and convoys."
    },
    {
        "name": "Bricks",
        "tier": 2,
        "composition": "Clay and Stone blocks fired in wood-kilns.",
        "purpose": "Permanent masonry construction.",
        "user_mechanics": "Provides superior fire resistance and structural stability compared to raw lumber."
    },
    {
        "name": "Charcoal",
        "tier": 2,
        "composition": "Partially burnt lumber processed in wood-kilns.",
        "purpose": "High-heat clean combustible fuel.",
        "user_mechanics": "Provides hotter, cleaner burn than raw wood for basic metal smelting."
    }
]

WILDLIFE = [
    # --- Unique Ostraka Wildlife ---
    {
        "name": "Sky-Grazer",
        "scientific_name": "Bovinus Aetheris",
        "role": "Atmospheric Processor / Livestock",
        "habitat": "Northern Outer Cliffs (High Altitude Clouds)",
        "danger_level": 2,
        "traits": "Docile floater. Excretes Voltaic Fleece filled with conductive St. Elmo's Fire gel. High explosive blowout risk if panicked.",
        "utility": "Fleece serves as reality-decay PPE once drained. Milk processed into fuel and Spark-Bread."
    },
    {
        "name": "Glimmer-Wings",
        "scientific_name": "Infectus lucis",
        "role": "Ambush Predator / Pest",
        "habitat": "Chaos-warped mountain peaks and storm clouds",
        "danger_level": 3,
        "traits": "Aggressive insect with shifting-light active camouflage wings.",
        "utility": "Pest control. Chitin can be harvested for camouflage dyes."
    },
    {
        "name": "Gritbore",
        "scientific_name": "Reptilis mineralis",
        "role": "Lithovorous Livestock / Scavenger",
        "habitat": "Iron Caldera outskirts and steppes",
        "danger_level": 2,
        "traits": "Rodent-like reptile with dense scales. Eats volcanic rocks to survive.",
        "utility": "Primary protein source and biomass fuel for laborers during Shadow Week."
    },
    {
        "name": "Ash-Bison",
        "scientific_name": "Bison Cinereus",
        "role": "Wild Migratory Herbivore",
        "habitat": "Open Steppes and volcanic zones",
        "danger_level": 4,
        "traits": "Massive bovine with 4 horns. Concrete Coat: Wallows in volcanic ash to form arrow-proof stone armor plates.",
        "utility": "Tanned stone-hide used for heavy shields/yurts. Ribs used as lumber for framing. Salty lean meat."
    },
    {
        "name": "Cloud-Cutter Ray",
        "scientific_name": "Aether-Manta",
        "role": "Apex Airborne Predator",
        "habitat": "Atmospheric currents & Hard Clouds",
        "danger_level": 5,
        "traits": "Massive ray spanning 2-3x human size. Bony crest for ramming hulls. Paralyzing tail stinger converts chaos-bleed into bio-electric voltage.",
        "utility": "Stingers harvested as weapons-grade contraband. Predicts storms by riding pressure wakes."
    },
    {
        "name": "Cloud-Ram",
        "scientific_name": "Capra ailurus",
        "role": "Mountain Livestock",
        "habitat": "Summit peaks of the Engineer's Mountain Range",
        "danger_level": 2,
        "traits": "Red panda head with ram horns. Powerful rabbit-like rear leaping legs. Double-layer windproof thermal wool.",
        "utility": "Wool harvested for high-grade Summit-Red textiles. Rich fatty milk used for long-lasting Peak-Cheese."
    },
    {
        "name": "Draft-Beetle",
        "scientific_name": "Coleoptera Gigas",
        "role": "Heavy Transport Organism",
        "habitat": "Canopy and Forest zones",
        "danger_level": 1,
        "traits": "Pony-sized green-black beetle. Legs have microscopic hooks to climb vertical branches while hauling cargo.",
        "utility": "Ranched by simians and opossums to pull branch-highway sleds. Shell harvested for roofing/shields."
    },
    {
        "name": "Dune Dog",
        "scientific_name": "Velcro-Catus deserti",
        "role": "Lethargic Insectivore",
        "habitat": "The Dust Bowl dunes",
        "danger_level": 1,
        "traits": "Round kitten-hedgehog-meerkat hybrid. Excretes shimmering heat-haze pheromone to lure bugs onto velcro-like fur.",
        "utility": "Valued domestic pet. Stained coats (Rust, Slag, Aether) used for specialized city pest control."
    },
    {
        "name": "Dust Skipper",
        "scientific_name": "Avis sabulo",
        "role": "Diving Scavenger / Fisher",
        "habitat": "Iron Caldera borders & mesas (Anvil Roosts)",
        "danger_level": 1,
        "traits": "Swept-wing kingfisher-like bird. Nictitating protective eye shields. Oil-slick feathers allow sand-diving.",
        "utility": "Nests serve as landmarks for convoys. Controls insect larvae and tick populations."
    },
    {
        "name": "Fur-Wyrm",
        "scientific_name": "Serpens villosus",
        "role": "Scavenger / Mountain Pest",
        "habitat": "Alpine forests, rocky crevices, and camps",
        "danger_level": 2,
        "traits": "Canine-headed serpent covered in grey fur. Slinks through crevices. Steals food, bites exposed toes for warmth.",
        "utility": "None (considered a campsite nuisance)."
    },
    {
        "name": "Furnace-Tick",
        "scientific_name": "Lithovore parasiticus",
        "role": "Industrial Lithovorous Barnacle",
        "habitat": "Iron Caldera mines and factory boilers",
        "danger_level": 3,
        "traits": "Horseshoe crab shape. Eats refined alloys and gathers on hot Aether-boilers, causing catastrophic overheating.",
        "utility": "Carapace is pure refined alloy from consumed metals; melted down as a recycling source."
    },
    {
        "name": "Gem-Shell Beetle",
        "scientific_name": "Coleoptera crystallinus",
        "role": "High-altitude Lithovore",
        "habitat": "Death Zone mountain altitudes",
        "danger_level": 2,
        "traits": "Carapace made of bio-crystallized gemstone/dragonstone. Threat response: angles shell to flash solar flare blinders.",
        "utility": "Primary food for ray fledglings. Crushed into 'Gem-Jam' to lure rays. Destructive pest to masonry."
    },
    {
        "name": "Glass-Scale Sand-Eel",
        "scientific_name": "Serpens vitreus",
        "role": "Subterranean Sand Predator",
        "habitat": "Dust Bowl and Sand Dunes",
        "danger_level": 5,
        "traits": "Females split at midsection into twin sand-anchoring tails. Males are 2-meter, two-headed monsters with fiberglass quills.",
        "utility": "Larvae ('Glass-Grubs') eaten by skippers. Mating thrashes create fatal Liquefaction pits."
    },
    {
        "name": "Night-Carapace",
        "scientific_name": "Coleoptera nox",
        "role": "Nocturnal Ambush Predator",
        "habitat": "Alpine Forests & high valleys",
        "danger_level": 4,
        "traits": "Bobcat-sized beetle with light-absorbing black shell. Serrated tendon-snipping mandibles.",
        "utility": "High-value luxury food. Sweet pork-lobster tasting meat prized in High-Roost restaurants."
    },
    {
        "name": "Abyssal Snail",
        "scientific_name": "Cochlea titanis",
        "role": "Heavy Draught Organism",
        "habitat": "Deep lakes, vortex swamps, and river beds",
        "danger_level": 1,
        "traits": "House-sized mollusk with immense, unstoppable traction torque. Unaffected by surface weather.",
        "utility": "Used for 'Snail-Draught' barge convoys."
    },
    {
        "name": "Weaver-Cow",
        "scientific_name": "Arachne grandis",
        "role": "Industrial Fiber Producer",
        "habitat": "High Peculiurus subterranean caverns",
        "danger_level": 3,
        "traits": "Giant spider sensitive to vibrations. Ranched exclusively by slow-moving Bradypods.",
        "utility": "Produces Silk-Steel (Iron-Weave) cables used for rigging and suspension bridges."
    },
    {
        "name": "Titan-Aphid",
        "scientific_name": "Aphis gigantus",
        "role": "Nectar Producer",
        "habitat": "Iron-Wood forests",
        "danger_level": 1,
        "traits": "Dog-sized insect. Taps iron-wood sap veins and excretes sweet honeydew fluid.",
        "utility": "Farmed by Formicidae to brew premium mead and sweeteners."
    },

    # --- Standard Stock Fantasy Wildlife ---
    {
        "name": "Timber Wolf",
        "scientific_name": "Canis lupus",
        "role": "Forest Pack Predator",
        "habitat": "Woodlands and low valleys",
        "danger_level": 3,
        "traits": "Standard wild pack hunter. Operates using group tactics to take down deer.",
        "utility": "Hides used for basic fur clothing; meat edible in emergencies."
    },
    {
        "name": "Wild Boar",
        "scientific_name": "Sus scrofa",
        "role": "Forest Herbivore / Scavenger",
        "habitat": "Undergrowth and oak woodlands",
        "danger_level": 2,
        "traits": "Aggressive when cornered. Thick hide and sharp tusks.",
        "utility": "Valuable source of fatty meat and thick leather."
    },
    {
        "name": "Red Deer",
        "scientific_name": "Cervus elaphus",
        "role": "Forest Herbivore",
        "habitat": "Valleys and grasslands",
        "danger_level": 1,
        "traits": "Skittish and fast. Males have large branching antlers.",
        "utility": "Primary game source for venison meat and antler tool-crafting."
    },
    {
        "name": "Peregrine Falcon",
        "scientific_name": "Falco peregrinus",
        "role": "Airborne Hunter",
        "habitat": "Cliffs and high canopy",
        "danger_level": 1,
        "traits": "High-velocity diving hunter targeting smaller birds.",
        "utility": "Trained by scouts and messengers for high-altitude hunting and communication."
    },
    {
        "name": "Black Bear",
        "scientific_name": "Ursus americanus",
        "role": "Valleys Omnivore",
        "habitat": "Riverbeds and thick woodlands",
        "danger_level": 3,
        "traits": "Solitary forager. Attacks when surprised or guarding cubs.",
        "utility": "Provides rich fat, thick winter hides, and meat."
    },
    {
        "name": "Domestic Sheep",
        "scientific_name": "Ovis aries",
        "role": "Domesticated Livestock",
        "habitat": "Settlement pastures and low hills",
        "danger_level": 0,
        "traits": "Placid herd animal requiring constant protection from wolves and wyrms.",
        "utility": "Primary source of basic wool, mutton, and milk for common populations."
    },
    {
        "name": "Draft Horse",
        "scientific_name": "Equus caballus",
        "role": "Domestic Beast of Burden",
        "habitat": "Farmlands and city roads",
        "danger_level": 1,
        "traits": "Large, muscular equine bred for heavy hauling and riding.",
        "utility": "Pulls wagons, carriages, and plows in areas without draft-beetle branches."
    }
]

FLORA = [
    # --- Unique Ostraka Flora ---
    {
        "name": "Grave-Roots",
        "classification": "Carnivorous Plant",
        "habitat": "Woodlands and near tectonic tear lines",
        "properties": "Mimics dead trees and stone-mimic timber. Utilizes root-based vibration sensing.",
        "applications": "Defensive barriers. Roots secrete a numbing toxin harvested for anesthetic use."
    },
    {
        "name": "Stone-Root",
        "classification": "Mineralized Timber",
        "habitat": "Rocky valleys and dry peaks",
        "properties": "Fossilized plant matter with high-molarity mineral veins. Completely fireproof and dense.",
        "applications": "Used for heavy construction, bridge anchors, and firearm furniture."
    },
    {
        "name": "Ghost Flower",
        "classification": "Volatile Alchemical Blossom",
        "habitat": "Dust Bowl high-static margins",
        "properties": "Highly susceptible to desiccation ('Dry Rot'). Swells with internal moisture.",
        "applications": "Refined into Aether-Clear medicine and luxury Void-Cream cosmetics."
    },
    {
        "name": "Strangler Fig",
        "classification": "Parasitic Arbor Vining",
        "habitat": "Arbor-Prime Canopy and old forests",
        "properties": "Spreads rapidly across wood-structures, locking and paralyzing mechanical elements.",
        "applications": "Used by the Silent Echo cult to sabotage and paralyze walking city mechanisms."
    },
    {
        "name": "Silver-Leaf",
        "classification": "Arcane Archive Tree",
        "habitat": "Steward vaults and old libraries",
        "properties": "Silver bark with vellum-like leaves that store memories via blue arcane pulses.",
        "applications": "Used to catalog historical records and weave psychic scroll archives."
    },
    {
        "name": "Saguaro Cactus-Kin",
        "classification": "Symbiotic Desert Succulent",
        "habitat": "The Dust Bowl",
        "properties": "Massive water-retentive structures with hard, spine-covered hides.",
        "applications": "Provides environmental ballast for skiffs. Internal cavity acts as a moisture shield for ghost flowers."
    },

    # --- Standard Stock Fantasy Flora ---
    {
        "name": "Common Oak",
        "classification": "Hardwood Tree",
        "habitat": "Valleys and temperate forests",
        "properties": "Durable, strong wood resistant to standard rot.",
        "applications": "Standard building lumber, furniture, ship beams, and firewood."
    },
    {
        "name": "Wild Rye",
        "classification": "Cereal Grain",
        "habitat": "Farmland plains and open valleys",
        "properties": "Resilient grass grain that grows in poor soil.",
        "applications": "Staple food crop used for flour, baking bread, and brewing standard ales."
    },
    {
        "name": "Bluebell",
        "classification": "Flowering Herb",
        "habitat": "Forest floor and shaded glades",
        "properties": "Fragrant spring flower, mildly toxic if ingested.",
        "applications": "Cultivated for decorative gardens and refined into light decorative perfumes."
    },
    {
        "name": "Forest Fern",
        "classification": "Spore Plant",
        "habitat": "Damp undergrowth and river margins",
        "properties": "Lush green fronds that absorb soil moisture.",
        "applications": "Used for packing fragile goods, animal bedding, and raw leaves boiled for basic green dye."
    },
    {
        "name": "Alpine Spruce",
        "classification": "Softwood Conifer",
        "habitat": "Mountain slopes and colder cliffs",
        "properties": "Straight-grained, flexible wood that burns hot and fast.",
        "applications": "Ideal for arrows, skiff masts, paper pulp, and resin collection."
    },
    {
        "name": "Desert Sage",
        "classification": "Shrub",
        "habitat": "Arid wastes and rocky hillsides",
        "properties": "Dry, aromatic bush containing volatile oils.",
        "applications": "Used as livestock feed, burnt as incense, and used to flavor smoked meats."
    }
]
