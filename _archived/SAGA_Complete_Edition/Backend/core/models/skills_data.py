"""
skills_data.py
Contains the massive B.R.U.T.A.L. Engine skill dictionary for use by the ActionResolver and AIDirector.
"""

SKILL_TRACKS = {
    "might_offense": {
        "name": "The Berserker",
        "category": "Offense",
        "base_stat": "might",
        "description": "Heavy/Crushing weapons. Cleaving through targets and shattering armor.",
        "skills": {}
    },
    "might_defense": {
        "name": "The Parrier",
        "category": "Defense",
        "base_stat": "might",
        "description": "Deflecting heavy blows by actively striking the enemy's weapon away.",
        "skills": {}
    },
    "might_utility": {
        "name": "Athletics",
        "category": "Utility",
        "base_stat": "might",
        "description": "Feats of raw strength, climbing, lifting, and breaking restraints.",
        "skills": {}
    },
    "might_magic": {
        "name": "School of Mass",
        "category": "Magic",
        "base_stat": "might",
        "description": "Manipulation of gravity, physical density, and kinetic force.",
        "skills": {}
    },
    "reflexes_offense": {
        "name": "The Ghost (The Breaker)",
        "category": "Offense",
        "base_stat": "reflexes",
        "description": "Bows/Thrown weapons. Extreme range and mobility-based skirmishing.",
        "skills": {
            "flurry": {
                "name": "Flurry",
                "stamina_cost": 1,
                "mechanic_tags": [
                    "dual_wield",
                    "minor_injury"
                ],
                "director_flavor": "The character blurs, executing a blistering secondary strike with their off-hand weapon in the same split second."
            },
            "hamstring": {
                "name": "Hamstring",
                "director_flavor": "Targeting mobility, the successful strike inflicts a Minor Injury to the legs, draining movement."
            },
            "kinetic_throw": {
                "name": "Kinetic Throw",
                "director_flavor": "Through pure kinetic control, the thrown weapon bounces off the target and arcs back into their hand."
            },
            "a_thousand_cuts": {
                "name": "A Thousand Cuts",
                "passive": True,
                "director_flavor": "Momentum builds\u2014a second consecutive hit violently upgrades from Minor to Major trauma."
            },
            "sonic_strike": {
                "name": "Sonic Strike",
                "focus_cost": 1,
                "mechanic_tags": [
                    "ignore_armor",
                    "confusion"
                ],
                "director_flavor": "Swinging fast enough to break the sound barrier, the deafening blow completely ignores armor."
            },
            "blink_step": {
                "name": "Blink Step",
                "move_cost": 1,
                "stamina_cost": 1,
                "director_flavor": "Vibrating across space, they instantly close the distance to strike in one fluid motion."
            },
            "arterial_slash": {
                "name": "Arterial Slash",
                "passive": True,
                "mechanic_tags": [
                    "bleed"
                ],
                "director_flavor": "Targeting the seams in armor, the slash causes catastrophic bleeding."
            },
            "ricochet_arc": {
                "name": "Ricochet Arc",
                "mechanic_tags": [
                    "aoe_minor"
                ],
                "director_flavor": "The weapon is hurled with insane velocity, ricocheting between multiple adjacent enemies."
            },
            "vibrating_edge": {
                "name": "Vibrating Edge",
                "passive": True,
                "mechanic_tags": [
                    "critical_limb_loss"
                ],
                "director_flavor": "Their blades vibrate into molecular saws; a critical hit severs a limb or vital artery."
            },
            "the_blender": {
                "name": "The Blender",
                "stamina_cost": 99,
                "mechanic_tags": [
                    "aoe_burst",
                    "major_injury",
                    "capstone"
                ],
                "director_flavor": "The character becomes a localized kinetic storm of blades, vibrating at terminal velocity and shredding everything in the zone."
            }
        }
    },
    "reflexes_defense": {
        "name": "The Ghost (The Bastion)",
        "category": "Defense",
        "base_stat": "reflexes",
        "description": "Unarmored Evasion. Dodging attacks completely and repositioning freely.",
        "skills": {
            "blur": {
                "name": "Blur",
                "passive": True,
                "director_flavor": "Their natural kinetic vibration makes them significantly harder to track."
            },
            "kinetic_dampening": {
                "name": "Kinetic Dampening",
                "director_flavor": "Vibrating at the exact moment of impact to bleed off physical momentum, downgrading the trauma."
            },
            "sidestep": {
                "name": "Sidestep",
                "stamina_cost": 1,
                "director_flavor": "A calculated, effortless shift in stance entirely avoids the ranged physical attack."
            },
            "afterimage": {
                "name": "Afterimage",
                "focus_cost": 1,
                "director_flavor": "Moving so fast they leave a visual echo, causing the enemy's attack to hit empty air."
            },
            "roll_with_the_punch": {
                "name": "Roll with the Punch",
                "passive": True,
                "director_flavor": "Riding the kinetic energy of a blow, they instantly slide backward out of range."
            },
            "vibration_ward": {
                "name": "Vibration Ward",
                "passive": True,
                "director_flavor": "Vibrating at a frequency that makes it impossible to hold, grapple, or pin them."
            },
            "deflect": {
                "name": "Deflect",
                "passive": True,
                "director_flavor": "They use their equipped light weapons to effortlessly swat physical projectiles out of the air."
            },
            "untouchable": {
                "name": "Untouchable",
                "passive": True,
                "director_flavor": "Untouched and moving at terminal speed, their movement is a total blur."
            },
            "phase_dodge": {
                "name": "Phase Dodge",
                "stamina_cost": 2,
                "director_flavor": "Vibrating completely out of sync with reality for a split second to take zero trauma from a lethal blow."
            },
            "ghost_in_the_machine": {
                "name": "Ghost in the Machine",
                "focus_cost": 99,
                "mechanic_tags": [
                    "capstone",
                    "invulnerable"
                ],
                "director_flavor": "Entering a state of absolute kinetic flow, the character becomes totally untouchable, weaving through the chaos like a ghost."
            }
        }
    },
    "reflexes_utility": {
        "name": "The Ghost (The Catalyst)",
        "category": "Utility",
        "base_stat": "reflexes",
        "description": "Moving silently, hiding in shadows, and physical acrobatics.",
        "skills": {
            "feather_fall": {
                "name": "Feather Fall",
                "passive": True,
                "director_flavor": "Unconsciously bleeding momentum, the character lands lightly without taking any falling damage."
            },
            "wall_run": {
                "name": "Wall Run",
                "move_cost": 1,
                "director_flavor": "Defying gravity, the character sprints horizontally across the vertical surface."
            },
            "lightning_reflexes": {
                "name": "Lightning Reflexes",
                "passive": True,
                "director_flavor": "Their nervous system fires impossibly fast, ensuring they always react before the enemy."
            },
            "sleight_of_hand": {
                "name": "Sleight of Hand",
                "director_flavor": "Hands blurring, they manipulate objects before the naked eye can catch the movement."
            },
            "vibration_sense": {
                "name": "Vibration Sense",
                "director_flavor": "Pressing a hand to the surface, they map the exact location and weight of everything moving nearby."
            },
            "sonic_hush": {
                "name": "Sonic Hush",
                "passive": True,
                "director_flavor": "Vibrating perfectly to cancel out their own physical friction, making zero noise when moving."
            },
            "kinetic_transfer": {
                "name": "Kinetic Transfer",
                "director_flavor": "Touching an ally, they transfer their raw physical momentum directly into them."
            },
            "escape_artist": {
                "name": "Escape Artist",
                "director_flavor": "Dislocating joints in a fraction of a second to instantly slip out of physical binds."
            },
            "hyper_metabolism": {
                "name": "Hyper-Metabolism",
                "passive": True,
                "director_flavor": "Their body processes and flushes toxins at an accelerated, superhuman rate."
            },
            "time_dilation": {
                "name": "Time Dilation",
                "focus_cost": 99,
                "stamina_cost": 99,
                "mechanic_tags": [
                    "capstone",
                    "time_stop"
                ],
                "director_flavor": "Perception accelerates so drastically that the world freezes entirely, leaving them the only one moving."
            }
        }
    },
    "reflexes_magic": {
        "name": "School of Motus",
        "category": "Magic",
        "base_stat": "reflexes",
        "description": "Control over velocity, acceleration, and kinetic momentum.",
        "skills": {}
    },
    "finesse_offense": {
        "name": "The Razor (The Breaker)",
        "category": "Offense",
        "base_stat": "finesse",
        "description": "Rapiers/Light Blades. Precision strikes and armor penetration.",
        "skills": {
            "precision_strike": {
                "name": "Precision Strike",
                "passive": True,
                "director_flavor": "Striking exactly where the armor plates meet to ignore all physical mitigation."
            },
            "hamstring_shot": {
                "name": "Hamstring Shot",
                "director_flavor": "A pinpoint ranged attack to the leg instantly drains the target's mobility."
            },
            "riposte": {
                "name": "Riposte",
                "stamina_cost": 1,
                "director_flavor": "Deflecting an attack and instantly launching an out-of-turn counter-strike."
            },
            "molecular_edge": {
                "name": "Molecular Edge",
                "focus_cost": 1,
                "director_flavor": "Honing the blade to an atom-thin edge to guarantee a Major Injury."
            },
            "disarm": {
                "name": "Disarm",
                "director_flavor": "Targeting the tendons in the wrist to force the enemy to drop their weapon."
            },
            "pinning_shot": {
                "name": "Pinning Shot",
                "director_flavor": "Pinning the target's clothing or limb directly to the environment with a projectile."
            },
            "destabilizing_wound": {
                "name": "Destabilizing Wound",
                "passive": True,
                "mechanic_tags": [
                    "bleed"
                ],
                "director_flavor": "The precise cut alchemically unbinds tissue; the wound refuses to clot."
            },
            "snipers_mark": {
                "name": "Sniper's Mark",
                "move_cost": 1,
                "director_flavor": "Remaining perfectly still to line up a devastating, perfectly aimed shot."
            },
            "heart_seeker": {
                "name": "Heart-Seeker",
                "passive": True,
                "director_flavor": "Exploiting the space between ribs to instantly critically injure an unaware target."
            },
            "telefrag": {
                "name": "Telefrag",
                "stamina_cost": 99,
                "mechanic_tags": [
                    "capstone",
                    "instant_kill",
                    "ignore_thresholds"
                ],
                "director_flavor": "The character materializes violently inside the target's physical space, forcing their atoms apart from the inside in an explosion of gore."
            }
        }
    },
    "finesse_defense": {
        "name": "The Razor (The Bastion)",
        "category": "Defense",
        "base_stat": "finesse",
        "description": "Counter-attacking. Punishing enemies who miss their strikes.",
        "skills": {
            "parry": {
                "name": "Parry",
                "stamina_cost": 1,
                "director_flavor": "Batting an incoming melee attack away with a dueling blade to entirely negate the trauma."
            },
            "liquefy": {
                "name": "Liquefy",
                "passive": True,
                "director_flavor": "Turning momentarily malleable, allowing piercing weapons to pass partially through liquid flesh."
            },
            "frictionless": {
                "name": "Frictionless",
                "passive": True,
                "director_flavor": "Altering surface friction to become categorically immune to grapples and pins."
            },
            "phase_step": {
                "name": "Phase-Step",
                "focus_cost": 1,
                "director_flavor": "Instantly folding space to teleport to an adjacent zone, leaving the attack to hit empty air."
            },
            "refract": {
                "name": "Refract",
                "passive": True,
                "director_flavor": "Bending the space around their body to drastically throw off ranged attacks."
            },
            "riposte_guard": {
                "name": "Riposte Guard",
                "passive": True,
                "director_flavor": "A defensive stance that acts as a trap, instantly cutting any enemy who misses a melee strike."
            },
            "liquid_evasion": {
                "name": "Liquid Evasion",
                "passive": True,
                "director_flavor": "Flowing around area-of-effect damage, drastically reducing blast trauma."
            },
            "molecular_shift": {
                "name": "Molecular Shift",
                "director_flavor": "Phasing vital organs out of the weapon's path to reduce a Critical Injury to a Minor one."
            },
            "slippery_target": {
                "name": "Slippery Target",
                "passive": True,
                "director_flavor": "Every movement grants a cumulative evasion bonus as they slide through the battlefield."
            },
            "untethered": {
                "name": "Untethered",
                "focus_cost": 99,
                "mechanic_tags": [
                    "capstone",
                    "invulnerable",
                    "ethereal"
                ],
                "director_flavor": "Stepping completely out of phase with the physical world, they walk through solid walls and enemy blades as an untouchable phantom."
            }
        }
    },
    "finesse_utility": {
        "name": "The Razor (The Catalyst)",
        "category": "Utility",
        "base_stat": "finesse",
        "description": "Picking locks, disarming mechanisms, and pickpocketing.",
        "skills": {
            "grip_and_slip": {
                "name": "Grip & Slip",
                "passive": True,
                "director_flavor": "Altering friction, they traverse impossible surfaces with ease."
            },
            "reshape": {
                "name": "Reshape",
                "stamina_cost": 0,
                "director_flavor": "Inanimate matter yields to them like wet clay."
            },
            "perfect_balance": {
                "name": "Perfect Balance",
                "passive": True,
                "director_flavor": "They walk the razor's edge with absolute, inhuman stability."
            },
            "liquid_egress": {
                "name": "Liquid Egress",
                "stamina_cost": 0,
                "director_flavor": "Bones dislocate and flesh liquefies as they squeeze through the impossibly small opening."
            },
            "phase_reach": {
                "name": "Phase-Reach",
                "focus_cost": 1,
                "director_flavor": "Their arm phases directly through the solid matter to grasp what lies beyond."
            },
            "saboteurs_eye": {
                "name": "Saboteur's Eye",
                "passive": True,
                "director_flavor": "A glance reveals the hidden linchpin holding the mechanism together."
            },
            "acrobatic_vault": {
                "name": "Acrobatic Vault",
                "stamina_cost": 0,
                "director_flavor": "Manipulating gravity, they execute a massive, graceful leap over the battlefield."
            },
            "silent_step": {
                "name": "Silent Step",
                "passive": True,
                "director_flavor": "Every footstep is rendered totally frictionless and silent."
            },
            "transmute_matter": {
                "name": "Transmute Matter",
                "stamina_cost": 0,
                "director_flavor": "The solid object dissolves into a swirling liquid or gas for safe storage."
            },
            "spatial_fold": {
                "name": "Spatial Fold",
                "focus_cost": 99,
                "mechanic_tags": [
                    "capstone",
                    "create_portal"
                ],
                "director_flavor": "The character rips the geometry of the map apart, forging a permanent two-way tear in reality."
            }
        }
    },
    "finesse_magic": {
        "name": "School of Flux",
        "category": "Magic",
        "base_stat": "finesse",
        "description": "Phase shifting, liquid manipulation, and matter alteration.",
        "skills": {}
    },
    "endurance_offense": {
        "name": "The Phalanx",
        "category": "Offense",
        "base_stat": "endurance",
        "description": "Shield-bashing, shoving, and utilizing heavy polearms to control space.",
        "skills": {
            "pike_wall": {
                "name": "Pike Wall",
                "director_flavor": "Set a polearm or heavy weapon to receive a charging enemy. Scaling Effort increases the physical trauma inflicted when an enemy enters your melee range. 8. Batter: Deliver repeated, heavy, exhausting blows against a target's shield or armor. Scaling Effort increases the Stamina drained directly from the target. 9. Impale: Pin an enemy to the ground or a wall with a polearm. Scaling Effort dictates the difficulty for them to pull free, or the number of Move Beats they lose."
            }
        }
    },
    "endurance_defense": {
        "name": "The Ironclad",
        "category": "Defense",
        "base_stat": "endurance",
        "description": "Medium Armor mastery. Reducing stamina drain from prolonged fights.",
        "skills": {
            "ablative_guard": {
                "name": "Ablative Guard",
                "director_flavor": "Angle your heavy armor to turn a direct hit into a glancing blow. Scaling Effort downgrades the incoming physical Injury tier. 5. Phalanx: Physically step in with your shield to cover a teammate. Scaling Effort increases the defensive bonus or direct mitigation granted to an adjacent ally. 6. Pain Suppression: Ignore the agonizing penalties of your wounds. Scaling Effort increases the number of rounds you can operate without losing Action Beats from Major Injuries."
            }
        }
    },
    "endurance_utility": {
        "name": "Survival",
        "category": "Utility",
        "base_stat": "endurance",
        "description": "Foraging, tracking weather, and enduring extreme environmental hazards.",
        "skills": {
            "forced_march": {
                "name": "Forced March",
                "director_flavor": "Push your biology through extreme exhaustion. Scaling Effort increases the hours you can march or the weight you can carry without suffering fatigue penalties."
            },
            "hardened_lungs": {
                "name": "Hardened Lungs",
                "director_flavor": "Hold your breath or resist airborne toxins. Scaling Effort increases the duration of oxygen deprivation survived or your resistance to poisonous environments."
            },
            "structural_brace": {
                "name": "Structural Brace",
                "director_flavor": "Reinforce a doorway or barricade using your own body weight. Scaling Effort increases the structural integrity or the sheer force required for enemies to break through."
            },
            "the_anvil": {
                "name": "The Anvil",
                "director_flavor": "You have mastered absolute attrition. When reduced to your final Health threshold, you can spend all remaining Stamina to become an immovable object. For the rest of the encounter, you cannot be incapacitated by physical trauma; you remain standing and fighting until the battle ends, regardless of the Critical Injuries sustained.",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "endurance_magic": {
        "name": "School of Ordo",
        "category": "Magic",
        "base_stat": "endurance",
        "description": "Stasis, preservation, and nullification of dynamic forces.",
        "skills": {}
    },
    "fortitude_offense": {
        "name": "The Juggernaut",
        "category": "Offense",
        "base_stat": "fortitude",
        "description": "Unarmed/Slam attacks. Using raw mass to trample and crush enemies.",
        "skills": {
            "momentum_swing": {
                "name": "Momentum Swing",
                "director_flavor": "Maximize the kinetic energy of an exotic spinning weapon (flail, chain). Scaling Effort increases the damage scaling specifically against enemies attempting to block with a shield. 8. Suppressive Fire: Unleash a deafening hail of projectiles to keep heads down. Scaling Effort increases the penalty applied to enemy attack rolls in the targeted Zone. 9. Shrapnel Burst: Fire an explosive or scatter-shot at close range. Scaling Effort increases the area of effect and the minor trauma inflicted on secondary targets."
            }
        }
    },
    "fortitude_defense": {
        "name": "The Sentinel",
        "category": "Defense",
        "base_stat": "fortitude",
        "description": "Heavy Armor/Carapace. Passively absorbing massive damage thresholds.",
        "skills": {
            "grit": {
                "name": "Grit",
                "director_flavor": "Bite down on the pain and brace your core. Scaling Effort downgrades the trauma tier of incoming blunt-force or explosive damage. 5. Unflinching: Keep your eyes open and weapon steady during absolute chaos. Scaling Effort increases your resistance to being blinded, deafened, or staggered by explosions or loud noises. 6. Inertia: Use the sheer weight of your exotic gear to anchor yourself. Scaling Effort increases your resistance to forced movement or being knocked prone."
            }
        }
    },
    "fortitude_utility": {
        "name": "Labor",
        "category": "Utility",
        "base_stat": "fortitude",
        "description": "Carrying massive loads, ignoring exhaustion, and physical resistance to pain.",
        "skills": {
            "weather_the_storm": {
                "name": "Weather the Storm",
                "director_flavor": "Press forward through extreme weather or punishing terrain. Scaling Effort increases your movement speed through environmental hazards."
            },
            "iron_grip": {
                "name": "Iron Grip",
                "director_flavor": "Hold onto a rope, a cliff edge, or a writhing beast. Scaling Effort increases the physical force required for an enemy or hazard to break your hold."
            },
            "heavy_recoil": {
                "name": "Heavy Recoil",
                "director_flavor": "Manage the immense kickback of personal artillery or explosive ordnance. Scaling Effort increases your accuracy when firing heavy weapons without bracing first."
            },
            "the_juggernaut": {
                "name": "The Juggernaut",
                "director_flavor": "You become a walking siege engine. Spend all remaining Stamina. You can walk straight through standard barricades, locked doors, and light walls without spending attacks. Any enemy attempting to physically block your movement automatically suffers a Major Injury from the impact.",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "fortitude_magic": {
        "name": "School of Lex",
        "category": "Magic",
        "base_stat": "fortitude",
        "description": "The imposition of absolute rules and unbreakable physical barriers.",
        "skills": {}
    },
    "vitality_offense": {
        "name": "The Blood-Hunter",
        "category": "Offense",
        "base_stat": "vitality",
        "description": "Sacrificing one's own HP to inflict massive, savage damage spikes.",
        "skills": {
            "grapple": {
                "name": "Grapple",
                "director_flavor": "Lock an enemy in a brutal biological hold. Scaling Effort increases the difficulty for the enemy to break the hold or escape your Zone. 8. Feral Strike: Execute unarmed attacks using bone, teeth, or raw body weight. Scaling Effort increases the raw physical trauma tier inflicted without a weapon. 9. Chokehold: Cut off air or blood flow to the brain. Scaling Effort increases the Composure or Stamina drain the target suffers while successfully grappled."
            }
        }
    },
    "vitality_defense": {
        "name": "The Regenerator",
        "category": "Defense",
        "base_stat": "vitality",
        "description": "Rapid biological healing. Clearing trauma tokens quickly during combat.",
        "skills": {
            "clot": {
                "name": "Clot",
                "director_flavor": "Flex your musculature to physically seal open wounds. Scaling Effort directly restores lost Stamina caused by active bleeding effects. 5. Feral Resilience: Fall back on primal survival instincts when cornered. Scaling Effort increases your physical mitigation specifically when you are suffering from a Major Injury. 6. Iron Gut: Resist ingested hazards or extreme environmental exposure. Scaling Effort increases your resistance to starvation, severe dehydration, or temperature extremes."
            }
        }
    },
    "vitality_utility": {
        "name": "Husbandry",
        "category": "Utility",
        "base_stat": "vitality",
        "description": "Taming, handling, and understanding the mutated beasts of the wastes.",
        "skills": {
            "forage": {
                "name": "Forage",
                "director_flavor": "Identify safe food, water, and medicinal flora in hostile territory. Scaling Effort increases the amount of supplies found or their healing quality."
            },
            "field_medic": {
                "name": "Field Medic",
                "director_flavor": "Bind wounds and set bones rapidly with bare hands and scavenged cloth. Scaling Effort increases the amount of bleeding stopped or the speed of stabilization."
            },
            "toxin_flush": {
                "name": "Toxin Flush",
                "director_flavor": "Force your metabolism to aggressively sweat out poisons. Scaling Effort reduces the duration or severity of an ingested poison or disease."
            },
            "apex_predator": {
                "name": "Apex Predator",
                "director_flavor": "You shatter your biological limits. Spend all remaining Stamina to tap into primal adrenaline. You instantly stabilize all bleeding, ignore all mechanical Injury penalties, and your unarmed strikes count as Heavy weapons for the remainder of the encounter.",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "vitality_magic": {
        "name": "School of Vita",
        "category": "Magic",
        "base_stat": "vitality",
        "description": "Biomancy, flesh-warping, and the manipulation of life-force.",
        "skills": {}
    },
    "logic_offense": {
        "name": "The Tactician",
        "category": "Offense",
        "base_stat": "logic",
        "description": "Traps and Explosives. Setting up calculated kill-zones.",
        "skills": {
            "ricochet": {
                "name": "Ricochet",
                "director_flavor": "Bounce a thrown weapon or projectile off the environment to hit a hidden target. Scaling Effort increases the angles calculated and the amount of physical cover bypassed. 8. Acoustic Dissonance: Create a loud, mathematically jarring distraction using the environment. Scaling Effort increases the \"Confusion\" Composure damage inflicted on targets. 9. Flanking Maneuver: Position yourself mathematically to cut off all escape vectors. Scaling Effort reduces the target's available Move Beats for their next turn."
            }
        }
    },
    "logic_defense": {
        "name": "The Strategist",
        "category": "Defense",
        "base_stat": "logic",
        "description": "Predictive positioning. Using geometry to force disadvantage on attackers.",
        "skills": {
            "predictive_evasion": {
                "name": "Predictive Evasion",
                "director_flavor": "Move to the exact coordinate where the attack mathematically won't be. Scaling Effort increases your Dodge threshold against area-of-effect or ranged attacks. 5. Deflection Angle: Angle a shield or blade to perfectly redirect force away from your center of mass. Scaling Effort downgrades the physical trauma of an incoming heavy strike. 6. Rationalize: Break down a terrifying supernatural event into cold, hard facts. Scaling Effort downgrades the Composure damage caused by intimidation or horror."
            }
        }
    },
    "logic_utility": {
        "name": "Engineering",
        "category": "Utility",
        "base_stat": "logic",
        "description": "Crafting, repairing machinery, and understanding complex architecture.",
        "skills": {
            "calculate_trajectory": {
                "name": "Calculate Trajectory",
                "director_flavor": "Determine the exact path of a projectile or falling object. Scaling Effort increases the accuracy of your throws or the warning time given to allies."
            },
            "assess_value": {
                "name": "Assess Value",
                "director_flavor": "Instantly estimate the structural integrity, monetary value, or utility of an object. Scaling Effort increases the exact detail and hidden properties revealed."
            },
            "coordinate": {
                "name": "Coordinate",
                "director_flavor": "Direct allies into optimal geometric positions. Scaling Effort grants bonus Move Beats to designated allies who follow your command."
            },
            "the_grand_equation": {
                "name": "The Grand Equation",
                "director_flavor": "You perfectly calculate the battlefield. Spend all remaining Focus. For one full round, every action taken by your allies succeeds optimally, and every action taken by the enemy is met with the most statistically punishing counter-measure (Advantage for all allies, Disadvantage for all enemies).",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "logic_magic": {
        "name": "School of Ratio",
        "category": "Magic",
        "base_stat": "logic",
        "description": "Geometric constructs, pure calculation, and spatial distortion.",
        "skills": {}
    },
    "knowledge_offense": {
        "name": "The Alchemist",
        "category": "Offense",
        "base_stat": "knowledge",
        "description": "Toxic Vials and Acids. Inflicting continuous trauma tokens and debuffs.",
        "skills": {
            "anatomical_strike": {
                "name": "Anatomical Strike",
                "director_flavor": "Direct a physical attack exactly where the organs are unprotected. Scaling Effort increases the physical armor mitigation completely bypassed. 8. Toxic Coating: Apply an alchemical irritant to your weapon. Scaling Effort increases the Composure drain (Disgust/Nausea) inflicted upon a successful hit. 9. Jury-Rig Trap: Set a rapid snare, tripwire, or explosive using the environment. Scaling Effort increases the trauma inflicted when the enemy triggers the trap."
            }
        }
    },
    "knowledge_defense": {
        "name": "The Artificer",
        "category": "Defense",
        "base_stat": "knowledge",
        "description": "Deployable cover. Throwing down temporary barricades or smoke screens.",
        "skills": {
            "tactical_anticipation": {
                "name": "Tactical Anticipation",
                "director_flavor": "Read the enemy's stance and footwork to predict their strike. Scaling Effort increases your Dodge threshold against that specific target. 5. Formulate Antidote: Quickly mix and administer a counter-agent. Scaling Effort increases the effectiveness of neutralizing a toxin or venom affecting you or an ally. 6. Mental Compartmentalization: Block out pain and horror using pure clinical detachment. Scaling Effort downgrades the tier of incoming Composure trauma."
            }
        }
    },
    "knowledge_utility": {
        "name": "Medicine",
        "category": "Utility",
        "base_stat": "knowledge",
        "description": "Anatomy, biological stabilization, and crafting remedies.",
        "skills": {
            "recall": {
                "name": "Recall",
                "director_flavor": "Access memorized maps, histories, or creature weaknesses. Scaling Effort increases the specificity and immediate tactical value of the information remembered."
            },
            "alchemy": {
                "name": "Alchemy",
                "director_flavor": "Mix scavenged materials into rudimentary explosives, acids, or salves. Scaling Effort increases the potency, damage, or healing duration of the crafted item."
            },
            "saboteur": {
                "name": "Saboteur",
                "director_flavor": "Identify the critical linchpin in a structure or mechanism. Scaling Effort increases the speed at which you can cleanly dismantle it."
            },
            "s_flaw": {
                "name": "s Flaw",
                "director_flavor": "You identify the single, catastrophic flaw in an enemy's defense or a fortified structure. Spend all remaining Focus. The next attack made against that target by you or an ally is an automatic, unmitigable Critical hit.",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "knowledge_magic": {
        "name": "School of Nexus",
        "category": "Magic",
        "base_stat": "knowledge",
        "description": "Portals, summoning, and planar gates.",
        "skills": {}
    },
    "awareness_offense": {
        "name": "The Overwatch",
        "category": "Offense",
        "base_stat": "awareness",
        "description": "Ambushes. Gaining massive damage bonuses against unalerted targets.",
        "skills": {
            "called_shot": {
                "name": "Called Shot",
                "director_flavor": "Target a specific, small vulnerability (an eye slit, an unbuckled strap). Scaling Effort increases the severity of the localized physical Injury inflicted. 8. Distract: Throw an object or reflect light to force an enemy to look away. Scaling Effort increases the penalty applied to the enemy's next defensive roll. 9. Expose: Reveal a hidden or invisible enemy's location to your party. Scaling Effort increases the duration the enemy remains exposed and unable to benefit from stealth."
            }
        }
    },
    "awareness_defense": {
        "name": "The Precog",
        "category": "Defense",
        "base_stat": "awareness",
        "description": "Unflankable. Cannot be surprised or ambushed by hidden enemies.",
        "skills": {
            "uncanny_dodge": {
                "name": "Uncanny Dodge",
                "director_flavor": "React to an attack you couldn't fully see coming. Scaling Effort increases your Dodge threshold against stealth attacks, snipers, or traps. 5. Flash/Smoke Screen: Deploy a blinding powder or smoke bomb to obscure vision. Scaling Effort increases the duration and radius of the obscurement. 6. Grounding Focus: Focus intensely on a specific, mundane detail to prevent sensory overload. Scaling Effort downgrades incoming Composure damage from chaotic or distracting sources."
            }
        }
    },
    "awareness_utility": {
        "name": "Scouting",
        "category": "Utility",
        "base_stat": "awareness",
        "description": "Tracking footprints, noticing hidden compartments, and heightened senses.",
        "skills": {
            "track": {
                "name": "Track",
                "director_flavor": "Read subtle signs of passage in the dirt or brush. Scaling Effort increases the age of the tracks you can follow or the details gleaned (size, weight, numbers)."
            },
            "vigilance": {
                "name": "Vigilance",
                "director_flavor": "Notice hidden threats, tripwires, or ambushes before they trigger. Scaling Effort increases the radius of your awareness in Zones."
            },
            "eavesdrop___lip_read": {
                "name": "Eavesdrop / Lip Read",
                "director_flavor": "Gather information from afar. Scaling Effort increases the distance you can effectively observe or listen through ambient noise."
            },
            "omnidirectional_sight": {
                "name": "Omnidirectional Sight",
                "director_flavor": "You enter a state of hyper-awareness. Spend all remaining Focus. You cannot be surprised, flanked, or hidden from. You may take an Attack of Opportunity against any enemy that moves within or into your Zone for the rest of the encounter without spending Beats.",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "awareness_magic": {
        "name": "School of Aura",
        "category": "Magic",
        "base_stat": "awareness",
        "description": "True sight, divination, and energy reading.",
        "skills": {}
    },
    "intuition_offense": {
        "name": "The Opportunist",
        "category": "Offense",
        "base_stat": "intuition",
        "description": "Dirty fighting. Exploiting environmental weaknesses or attacking blinded foes.",
        "skills": {
            "feint": {
                "name": "Feint",
                "director_flavor": "Trick an enemy into blocking the wrong way with a false tell. Scaling Effort increases the Advantage granted to your actual attack roll. 8. Jinx: Notice an environmental hazard (a loose rock, a weakened beam) and trigger it near the enemy. Scaling Effort increases the physical trauma the hazard inflicts. 9. Sow Doubt: Casually point out a flaw in the enemy's stance or plan during combat. Scaling Effort increases the \"Self-Doubt\" Composure drain inflicted."
            }
        }
    },
    "intuition_defense": {
        "name": "The Survivor",
        "category": "Defense",
        "base_stat": "intuition",
        "description": "Luck-based evasion. Narrowly escaping lethal blows through pure instinct.",
        "skills": {
            "blind_luck": {
                "name": "Blind Luck",
                "director_flavor": "Stumble, slip, or coincidentally drop your guard at the exact perfect moment to avoid a lethal blow. Scaling Effort downgrades an incoming Major or Critical Injury to a Minor one. 5. Read the Tell: Anticipate an enemy's attack by reading their eyes and body language. Scaling Effort increases your Dodge threshold against that specific enemy. 6. Shake it Off: Dismiss a supernatural or psychological dread as just a \"bad feeling.\" Scaling Effort downgrades incoming Composure trauma."
            }
        }
    },
    "intuition_utility": {
        "name": "Scavenging",
        "category": "Utility",
        "base_stat": "intuition",
        "description": "Streetwise bartering, finding valuable salvage, and reading people.",
        "skills": {
            "gut_check": {
                "name": "Gut Check",
                "director_flavor": "Get a visceral read on whether a person is lying or a situation is a trap. Scaling Effort increases the clarity and specificity of the instinct.\nScavenger's Luck: Find useful items in entirely barren environments. Scaling Effort increases the rarity or immediate utility of the scavenged gear."
            },
            "synchronicity": {
                "name": "Synchronicity",
                "director_flavor": "Act perfectly in tandem with an ally without speaking a word. Scaling Effort allows you to share Focus or Stamina Beats directly with that ally."
            },
            "the_winning_hand": {
                "name": "The Winning Hand",
                "director_flavor": "You perfectly read the flow of fate. Spend all remaining Focus. You may dictate the exact result of the next die roll made by either you or the GM (declaring an automatic critical success for you, or a catastrophic critical failure for the enemy).",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "intuition_magic": {
        "name": "School of Omen",
        "category": "Magic",
        "base_stat": "intuition",
        "description": "Probability manipulation, fate, and luck weaving.",
        "skills": {}
    },
    "willpower_offense": {
        "name": "The Vanguard",
        "category": "Offense",
        "base_stat": "willpower",
        "description": "Fear-inducing strikes. Physically damages while crushing enemy Composure.",
        "skills": {
            "intimidate": {
                "name": "Intimidate",
                "director_flavor": "Project overwhelming dread and authority. Scaling Effort increases the \"Intimidation\" Composure damage inflicted. 8. Relentless Pursuit: Mark a target and mentally refuse to let them escape. Scaling Effort grants you bonus Move Beats that can only be used to move directly toward that specific target. 9. Brutal Takedown: Execute a vicious, terrifying physical strike meant to send a message. Scaling Effort increases the physical trauma inflicted and causes splash Composure damage to nearby enemies who witness it."
            }
        }
    },
    "willpower_defense": {
        "name": "The Resolve",
        "category": "Defense",
        "base_stat": "willpower",
        "description": "Ignoring pain. Fighting at full capacity even while critically wounded.",
        "skills": {
            "mental_fortress": {
                "name": "Mental Fortress",
                "director_flavor": "Lock your mind shut against psychological trauma or psychic intrusion. Scaling Effort downgrades incoming Composure Injuries. 5. Defiance: Stare down an attacker and brace for impact. Scaling Effort increases your physical mitigation as you tense your body through pure stubbornness. 6. Bite the Bullet: Perform field surgery on yourself or an ally without anesthetic. Scaling Effort increases the effectiveness of the healing while minimizing the Composure damage taken by the patient."
            }
        }
    },
    "willpower_utility": {
        "name": "Intimidation",
        "category": "Utility",
        "base_stat": "willpower",
        "description": "Interrogation, resisting coercion, and breaking an NPC's resolve.",
        "skills": {
            "iron_vow": {
                "name": "Iron Vow",
                "director_flavor": "Push through extreme physical pain or exhaustion through sheer mental force. Scaling Effort increases the mechanical Injury penalties you can temporarily ignore."
            },
            "interrogate": {
                "name": "Interrogate",
                "director_flavor": "Extract information from an unwilling subject through intense pressure. Scaling Effort increases the detail and truthfulness of the extracted intel."
            },
            "unyielding_stride": {
                "name": "Unyielding Stride",
                "director_flavor": "Refuse to be slowed down by the world. Scaling Effort allows you to completely ignore difficult terrain or encumbrance penalties."
            },
            "absolute_grit": {
                "name": "Absolute Grit",
                "director_flavor": "You refuse to break. Spend all remaining Focus. For the remainder of the encounter, your Composure threshold cannot be breached. You are immune to all fear, intimidation, and mental trauma, and your physical attacks gain Advantage driven by pure, unstoppable willpower.",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "willpower_magic": {
        "name": "School of Anumis",
        "category": "Magic",
        "base_stat": "willpower",
        "description": "Telepathy, mind domination, and psychic force.",
        "skills": {}
    },
    "charm_offense": {
        "name": "The Warlord",
        "category": "Offense",
        "base_stat": "charm",
        "description": "Companion Directives. Commanding pets or mercenaries in coordinated strikes.",
        "skills": {
            "command": {
                "name": "Command",
                "director_flavor": "Bark a military order so forcefully an enemy instinctively obeys for a split second. Scaling Effort dictates the complexity of the command (e.g., \"Drop it,\" \"Halt,\" \"Look away\"). 8. Demoralize: Taunt or mock an enemy to break their spirit. Scaling Effort increases the Composure trauma inflicted. 9. Incite: Turn an enemy's anger against one of their own allies through manipulation. Scaling Effort increases the chance they make a friendly-fire attack."
            }
        }
    },
    "charm_defense": {
        "name": "The Diplomat",
        "category": "Defense",
        "base_stat": "charm",
        "description": "Misdirection. Forcing an enemy to target a different ally or hesitate.",
        "skills": {
            "defuse": {
                "name": "Defuse",
                "director_flavor": "Talk an enemy down or cause them to hesitate right before they strike. Scaling Effort increases the chance they lose their Action Beat or redirect their attack. 5. Inspire Courage: Bolster an ally's resolve in the heat of battle. Scaling Effort grants a defensive bonus to an ally's Composure threshold. 6. The Martyr: Draw enemy attention to yourself using pure presence to save an ally. Scaling Effort increases the likelihood enemies target you instead of a vulnerable teammate."
            }
        }
    },
    "charm_utility": {
        "name": "Persuasion",
        "category": "Utility",
        "base_stat": "charm",
        "description": "De-escalation, diplomacy, and gathering information through social grace.",
        "skills": {
            "persuade_deceive": {
                "name": "Persuade/Deceive",
                "director_flavor": "Convince or lie to an NPC. Scaling Effort increases the believability of the lie or the magnitude of the favor requested."
            },
            "barter": {
                "name": "Barter",
                "director_flavor": "Negotiate better prices or trade salvage. Scaling Effort increases the monetary value gained or the resources saved."
            },
            "rally": {
                "name": "Rally",
                "director_flavor": "Inspire your allies outside of combat with a speech or shared moment. Scaling Effort restores lost Composure or Stamina thresholds during a short rest."
            },
            "s_decree": {
                "name": "s Decree",
                "director_flavor": "You command the absolute attention of the battlefield. Spend all remaining Focus. All enemies in the Zone must pass a massive Composure check or immediately surrender, flee, or drop their weapons in absolute Awe.",
                "mechanic_tags": [
                    "capstone"
                ]
            }
        }
    },
    "charm_magic": {
        "name": "School of Lux",
        "category": "Magic",
        "base_stat": "charm",
        "description": "Radiance, illusion, blinding presence, and hard-light constructs.",
        "skills": {}
    },
}

def get_skill_flavor(skill_name: str) -> str:
    """Helper to do a deep search for a skill name and return its flavor text."""
    if not skill_name:
        return ""
        
    lookup = skill_name.lower().replace(" ", "_").replace("'", "")
    
    for track_key, track_data in SKILL_TRACKS.items():
        skills = track_data.get("skills", {})
        if lookup in skills:
            return skills[lookup].get("director_flavor", "")
            
    return ""
