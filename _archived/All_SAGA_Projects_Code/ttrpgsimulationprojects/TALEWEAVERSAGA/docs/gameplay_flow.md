# TALEWEAVERS: Core Gameplay Loop & State Flow (GDD)

**Persona**: GameDesigner
**Status**: DRAFT v1.0

## 1. Design Pillars
*   **Tactical Friction**: Every action has a cost (Stamina/Focus). Players must manage resource attrition.
*   **Narrative Resonance**: The AI Director reacts to the *margin* of success, not just hit/miss.
*   **Scale Fluidity**: Seamless transition from world-traveling to tactical combat.

---

## 2. The Core Loops

### Moment-to-Moment (0–30 seconds)
*   **Action**: Player selects a "Lead & Trail" skill from the `ActionDeck`.
*   **Feedback**: Skill stats vs. Enemy defense are compared in a **Clash**. Visual margin-of-victory feedback (Graze, Normal, Critical).
*   **Reward**: Stamina/Focus drain from the enemy, HP reduction, or tactical positioning gain.

### Session Loop (5–30 minutes)
*   **Goal**: Navigate 1-3 Hexes or resolve a major Encounter.
*   **Tension**: Resource attrition (Stamina doesn't fully regenerate between tactical beats without rest).
*   **Resolution**: Looting, XP gain, or narrative progression via the Director's Log.

### Long-Term Loop (Hours–Weeks)
*   **Progression**: "Soulweave Evolution" - unlocking new tactical skill pips and attribute increases.
*   **Retention**: Shaping the world map via the "God Engine" results and persistent settlement state.

---

## 3. VTT Tier State Machine

The VTT consists of 5 tiers of granularity. Transitions are triggered by zoom level or explicit system events (Encounter Start).

| Tier | Scale | UI Component | Primary Gameplay |
| :--- | :--- | :--- | :--- |
| **T1** | Global | `MapRenderer` | World travel, regional discovery. |
| **T2** | Regional | `MapRenderer` | Point-of-interest identification. |
| **T3** | Local | `SurvivalScreen` | Resource gathering, campsite management. |
| **T4** | Exploration | `ExplorationNodeMap` | Dungeon crawling, building entry. |
| **T5** | Tactical | `PixiBattlemap` | Combat, high-stakes skill checks (Clash). |

### Phase Constraints
*   **EXPLORATION (T1-T4)**: Movement is free-form or node-based.
*   **TACTICAL (T5)**: Movement is grid-bound, turn-based, and stamina-calculated.
*   **DEPLOYMENT**: Occurs when transitioning from T4 -> T5. Players place tokens.

---

## 4. Lead & Trail Skill Logic

Skills are defined by two stats (e.g., `Might + Fortitude`). 
*   **Lead Stat**: Dictates the **Rank** (Lead / 5). This is the primary bonus.
*   **Trail Stat**: Dictates the **Pips** (Lead % 5). This provides minor bonuses or unlocks sub-features of the skill.

**ActionDeck Requirement**:
*   The UI must visually represent the "Pips" as slots that fill up based on the stat value.
*   Hovering over a skill should show the `Clash` margin thresholds (e.g., "Need 14+ for Critical").

---

## 5. Transition Rules
1.  **Zoom Down**: Triggers automatically as the camera nears the threshold.
2.  **Zoom Up**: Triggers automatically, but *disabled* if `inCombat === true`.
3.  **Force T5**: Triggered by the Director when an NPC/Enemy initiates a `Clash` encounter.
