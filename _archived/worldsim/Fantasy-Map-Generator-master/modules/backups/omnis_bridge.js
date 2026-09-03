/**
 * OMNIS BRIDGE
 * Injected natively into Azgaar's Fantasy Map Generator
 * Connects Azgaar's live simulation directly to the Python backend.
 */

(function initOmnisBridge() {
  console.log("Omnis Bridge: Initializing native integration...");

  // Create the Floating UI Panel
  const panel = document.createElement("div");
  panel.id = "omnis-control-panel";
  panel.style.cssText = `
    position: absolute;
    top: 20px;
    right: 20px;
    width: 320px;
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 12px;
    padding: 16px;
    color: #e2e8f0;
    font-family: 'Space Grotesk', system-ui, sans-serif;
    z-index: 99999;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    gap: 12px;
    user-select: none;
  `;

  panel.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
      <h2 style="margin: 0; font-size: 18px; font-weight: bold; background: linear-gradient(90deg, #a855f7, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">OMNIS ENGINE</h2>
      <div id="omnis-status-dot" style="width: 10px; height: 10px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 8px #ef4444;"></div>
    </div>
    
    <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px;">
      <button id="btn-sync" style="background: linear-gradient(90deg, #059669, #10b981); border: none; padding: 10px; border-radius: 6px; color: white; font-weight: bold; cursor: pointer; transition: all 0.2s;">
        📥 Sync Map to Python
      </button>
      
      <button id="btn-chaos" style="background: linear-gradient(90deg, #7e22ce, #a855f7); border: none; padding: 10px; border-radius: 6px; color: white; font-weight: bold; cursor: pointer; transition: all 0.2s;">
        🌀 Sear Chaos Spiral
      </button>
      
      <button id="btn-lore" style="background: linear-gradient(90deg, #b45309, #d97706); border: none; padding: 10px; border-radius: 6px; color: white; font-weight: bold; cursor: pointer; transition: all 0.2s;">
        🧬 Inject Ostraka Lore
      </button>
      
      <div style="display: flex; gap: 8px;">
        <button id="btn-tick" style="flex: 1; background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.5); padding: 8px; border-radius: 6px; color: #60a5fa; cursor: pointer; font-weight: bold;">
          ▶ Force Tick
        </button>
        <button id="btn-auto" style="flex: 1; background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5); padding: 8px; border-radius: 6px; color: #f87171; cursor: pointer; font-weight: bold;">
          Auto-Tick: OFF
        </button>
      </div>
    </div>

    <div style="font-size: 12px; color: #94a3b8; margin-top: 8px; font-family: monospace;">
      <div style="display: flex; justify-content: space-between;">
        <span>Sim Status:</span>
        <span id="omnis-status-text">Disconnected</span>
      </div>
      <div style="display: flex; justify-content: space-between;">
        <span>Global Chaos:</span>
        <span id="omnis-chaos">--%</span>
      </div>
    </div>
  `;

  document.body.appendChild(panel);

  // Logic bindings
  const btnSync = document.getElementById("btn-sync");
  const btnTick = document.getElementById("btn-tick");
  const btnAuto = document.getElementById("btn-auto");
  const statusDot = document.getElementById("omnis-status-dot");
  const statusText = document.getElementById("omnis-status-text");
  const chaosText = document.getElementById("omnis-chaos");

  let autoTickInterval = null;

  // Cache for the latest Omnis state so we can display it in tooltips
  let latestOmnisState = null;

  async function fetchAndApplySimState() {
    try {
      const res = await fetch("http://localhost:8000/api/state");
      if (res.ok) {
        statusDot.style.background = "#22c55e";
        statusDot.style.boxShadow = "0 0 8px #22c55e";
        statusText.innerText = "Connected & Synced";
        
        const data = await res.json();
        latestOmnisState = data.data.factions;
        chaosText.innerText = data.data.chaos_level ? Math.floor(data.data.chaos_level) + "%" : "42%";
        
        // Apply native layer data
        applyNativeLayers(latestOmnisState, data.data.fringe_groups, data.data.ecology_grid, data.data.resource_nodes, data.data.territory_changes, data.data.trade_routes);
        console.log("Omnis: Synced state from Python into UI.", latestOmnisState);
      }
    } catch (err) {
      statusDot.style.background = "#ef4444";
      statusDot.style.boxShadow = "0 0 8px #ef4444";
      statusText.innerText = "Offline";
      latestOmnisState = null;
    }
  }

  // Only check status once on load to see if backend is running. No constant polling!
  fetchAndApplySimState();

  const magistarColors = {
    "Stagus": "#a855f7",     // True Purple
    "Tiraton": "#c084fc",    // Light Purple
    "Gavusrix": "#d946ef",   // Fuchsia
    "Aurgenas": "#e879f9",   // Light Fuchsia
    "Lophex": "#ec4899",     // Pink
    "Tyrustis": "#f472b6",   // Light Pink
    "Opecten": "#9333ea",    // Dark Violet
    "Vecelo": "#db2777",     // Deep Pink
    "Termhill": "#7e22ce",   // Deep Purple
    "Carulkem": "#be185d",   // Dark Rose
    "Virantor": "#fdf4ff",   // Ghostly Violet
    "Metrion": "#86198f"     // Dark Fuchsia
  };

  function applyNativeLayers(factionsData, fringeGroupsData, ecologyGridData, resourceNodesData, territoryChangesData, tradeRoutesData) {
    if (!window.pack || !window.pack.cells || !window.pack.religions) return;
    
    // ============================================
    // 0. TERRITORY CONQUEST (Political Map Flipping)
    // ============================================
    if (territoryChangesData && territoryChangesData.length > 0) {
        let bordersChanged = false;
        territoryChangesData.forEach(change => {
            // Find the state id mapping in the frontend based on the backend ID or name
            // The backend passes 'new_faction' which corresponds to the state `i` if mapped properly, 
            // but the backend ID is the faction name currently. Let's look up the state `i` from states array.
            // Wait, new_faction is the faction id (name usually or index). Let's check backend ID.
            // backend passes faction.name or id. It's `new_faction: initiator.id` which is the name.
            const newState = window.pack.states.find(s => s.name === change.new_faction || s.i === change.new_faction);
            if (newState && window.pack.cells.state[change.cell_id] !== newState.i) {
                window.pack.cells.state[change.cell_id] = newState.i;
                bordersChanged = true;
            }
        });
        
        if (bordersChanged) {
            console.log("Omnis: Redrawing borders due to territory conquest!");
            if (window.drawBorders) window.drawBorders();
            if (window.drawStates) window.drawStates();
        }
    }
    
    // ============================================
    // 1. RELIGION LAYER (Cults & Wardens)
    // ============================================
    // Inject the 12 Cults + Wardens into pack.religions if they don't exist yet
    if (window.pack.religions.length < 13 || !window.pack.religions.find(r => r.name === "Cult of Stagus")) {
      const newReligions = [{ name: "No religion", i: 0 }];
      
      let index = 1;
      for (const [magistar, color] of Object.entries(magistarColors)) {
        newReligions.push({
          i: index,
          name: "Cult of " + magistar,
          type: "Cult",
          form: "Dark Cult",
          color: color,
          culture: 0,
          center: 0,
          expansion: "global",
          expansionism: 5
        });
        index++;
      }
      // Add the Wardens as Religion ID 13
      newReligions.push({
          i: index,
          name: "The Grey Wardens",
          type: "Cult",
          form: "Order",
          color: "#475569", // Slate Grey
          culture: 0,
          center: 0,
          expansion: "global",
          expansionism: 5
      });
      window.pack.religions = newReligions;
    }
    
    const wardenReligionId = window.pack.religions.find(r => r.name === "The Grey Wardens").i;

    factionsData.forEach(faction => {
      const state = window.pack.states.find(s => s.name === faction.name);
      if (!state) return;
      
      // -- Military Layer Injection --
      if (faction.military_power !== undefined) {
         // Clear old regiments
         state.military = [];
         
         // Create one massive regiment representing the Python army strength
         state.military.push({
             i: 0,
             a: faction.military_power * 100, // Multiply to make numbers feel realistic
             n: 0, 
             u: 0, 
             state: state.i, 
             cell: state.center, 
             name: state.name + " Grand Army", 
             icon: "⚔️"
         });
      }

      // -- Religion Layer (Cult & Warden Land Claims) --
      const stateCells = [];
      for (let i = 0; i < window.pack.cells.i.length; i++) {
        if (window.pack.cells.state[i] === state.i) {
          stateCells.push(i);
        }
      }
      
      if (stateCells.length > 0) {
          const cult = window.pack.religions.find(r => r.name === "Cult of " + faction.magistar_id);
          
          let numCorrupted = Math.floor(stateCells.length * (faction.cult_infiltration || 0));
          let numWardens = Math.floor(stateCells.length * (faction.warden_presence || 0));
          
          // Claim cells for Cult
          for (let i = 0; i < numCorrupted; i++) {
              if (cult) window.pack.cells.religion[stateCells[i]] = cult.i;
          }
          // Claim cells for Wardens (from the opposite end of the state cells array so they don't overlap perfectly)
          for (let i = 0; i < numWardens; i++) {
              window.pack.cells.religion[stateCells[stateCells.length - 1 - i]] = wardenReligionId;
          }
      }
    });
    
    // ============================================
    // 2. ZONES LAYER (Fringe Groups)
    // ============================================
    if (fringeGroupsData && fringeGroupsData.length > 0) {
        window.pack.zones = []; // Reset native zones
        window.pack.cells.zone = new Uint16Array(window.pack.cells.i.length); // Clear physical zones array
        
        let zoneIndex = 1; // Zones start at 1
        
        fringeGroupsData.forEach(fg => {
            const state = window.pack.states.find(s => s.name === fg.target);
            if (!state) return;
            
            // Create the native Zone object (Hatching = striped)
            window.pack.zones.push({
                i: zoneIndex,
                name: fg.name,
                color: fg.color,
                type: "Hatching" // "Hatching" creates diagonal striped overlays
            });
            
            // Find cells for this state and give a percentage of them to the zone
            const stateCells = [];
            for (let i = 0; i < window.pack.cells.i.length; i++) {
                if (window.pack.cells.state[i] === state.i) {
                   stateCells.push(i);
                }
            }
            
            // Fringe groups claim land visually based on their active influence over the faction
            const influence = fg.influence || 0.1;
            const numZoneCells = Math.floor(stateCells.length * influence);
            for (let i = 0; i < numZoneCells; i++) {
                window.pack.cells.zone[stateCells[i]] = zoneIndex;
            }
            
            zoneIndex++;
        });
    }
    
    // ============================================
    // 3. FLORA LAYER (Hijacking Provinces)
    // ============================================
    if (window.pack.provinces && ecologyGridData) {
        window.pack.provinces = [0]; // 0 is neutral
        window.pack.cells.province = new Uint16Array(window.pack.cells.i.length);
        
        const floraColors = ["#22c55e", "#10b981", "#14b8a6", "#84cc16", "#065f46"];
        const existingProvs = {};
        let provIndex = 1;
        
        for (const [cellId, eco] of Object.entries(ecologyGridData)) {
            if (eco.f) {
                if (!existingProvs[eco.f]) {
                    existingProvs[eco.f] = provIndex;
                    window.pack.provinces.push({
                        i: provIndex,
                        name: eco.f + " Bloom",
                        formName: "Bloom",
                        color: floraColors[provIndex % floraColors.length]
                    });
                    provIndex++;
                }
                window.pack.cells.province[cellId] = existingProvs[eco.f];
            }
        }
    }

    // ============================================
    // 4. FAUNA LAYER (Hijacking Cultures visually)
    // ============================================
    if (window.pack.cultures && ecologyGridData) {
        window.pack.cells.culture = new Uint16Array(window.pack.cells.i.length); // Clear visual map
        
        const faunaColors = ["#b45309", "#d97706", "#f59e0b", "#78350f", "#92400e", "#ea580c"];
        const existingCultures = {};
        let baseCultureIndex = window.pack.cultures.length;
        
        for (const [cellId, eco] of Object.entries(ecologyGridData)) {
            if (eco.a) {
                if (!existingCultures[eco.a]) {
                    // Check if already in pack.cultures
                    let existing = window.pack.cultures.find(c => c.name === eco.a + " Territory");
                    if (!existing) {
                        existing = {
                            i: baseCultureIndex,
                            name: eco.a + " Territory",
                            color: faunaColors[baseCultureIndex % faunaColors.length],
                            type: "Fauna",
                            expansionism: 1
                        };
                        window.pack.cultures.push(existing);
                        baseCultureIndex++;
                    }
                    existingCultures[eco.a] = existing.i;
                }
                window.pack.cells.culture[cellId] = existingCultures[eco.a];
            }
        }
    }

    // ============================================
    // 5. RESOURCE MARKERS (Permanent Nodes)
    // ============================================
    if (window.pack.markers && resourceNodesData) {
        // Clear old Omnis resource markers
        window.pack.markers = window.pack.markers.filter(m => m.type !== "OmnisResource");
        
        let markerIndex = window.pack.markers.length > 0 ? window.pack.markers[window.pack.markers.length - 1].i + 1 : 0;
        
        // Always draw the permanent resource nodes exactly where Python generated them
        resourceNodesData.forEach(node => {
            window.pack.markers.push({
                i: markerIndex++,
                icon: node.icon,
                x: window.pack.cells.p[node.cell][0],
                y: window.pack.cells.p[node.cell][1],
                cell: node.cell,
                type: "OmnisResource",
                dx: 50,
                dy: 50,
                px: 16,
                name: `${node.icon} ${node.name}`,
                notes: node.desc
            });
        });
    }

    // ============================================
    // 5. TRADE ROUTES
    // ============================================
    if (tradeRoutesData && window.pack && window.pack.cells) {
        const routesGroup = document.getElementById("routes");
        if (routesGroup) {
            // Clear previous Omnis trade routes
            routesGroup.querySelectorAll(".omnis-trade-route").forEach(el => el.remove());
            
            tradeRoutesData.forEach(routeObj => {
                const route = routeObj.path;
                const ttl = routeObj.ttl || 5;
                if (!route || route.length < 2) return;
                
                // route is an array of [x, y] in Python 100x100 grid coords.
                const points = route.map(coord => {
                    const px = (coord[0] / 100) * window.graphWidth;
                    const py = (coord[1] / 100) * window.graphHeight;
                    return `${px},${py}`;
                }).join(" ");
                
                const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
                polyline.setAttribute("points", points);
                polyline.setAttribute("stroke", "#facc15"); // gold
                polyline.setAttribute("stroke-width", "2");
                polyline.setAttribute("fill", "none");
                polyline.setAttribute("stroke-dasharray", "5,5");
                polyline.setAttribute("class", "omnis-trade-route");
                
                // Fade opacity based on TTL (5 -> 0.8, 1 -> 0.2)
                const opacity = Math.max(0.2, ttl * 0.16);
                polyline.setAttribute("opacity", opacity.toString());
                
                routesGroup.appendChild(polyline);
            });
        }
    }
    // 6. FORCE NATIVE REDRAWS
    // ============================================
    const toggles = ["toggleReligions", "toggleMilitary", "toggleZones", "toggleProvinces", "toggleCultures", "toggleMarkers"];
    toggles.forEach(id => {
        const btn = document.getElementById(id);
        if (btn && btn.classList.contains("active")) {
            btn.click(); setTimeout(() => btn.click(), 50);
        }
    });
  }

  // Hijack Azgaar's tooltip to show Omnis stats!
  // Azgaar uses d3 events. We will add a global mouseover listener to the map SVG.
  document.addEventListener('mouseover', (e) => {
    if (!latestOmnisState || !window.pack || !window.pack.states) return;
    
    // Azgaar states are usually paths inside #states, or text labels.
    const target = e.target;
    if (target && target.tagName === 'path' && target.parentElement && target.parentElement.id === 'statesBody') {
      const stateId = parseInt(target.id.replace('state', ''));
      if (isNaN(stateId)) return;
      
      const azgaarState = window.pack.states[stateId];
      if (!azgaarState) return;
      
      // Match Azgaar State Name to Omnis Faction Name
      const omnisFaction = latestOmnisState.find(f => f.name === azgaarState.name) || latestOmnisState[stateId - 1];
      
      if (omnisFaction) {
        // Find Azgaar's custom tooltip element
        const tooltip = document.getElementById('tooltip');
        if (tooltip) {
          // Append our custom stats!
          const omnisHtml = `<br><hr style="border:0; border-top:1px solid #444; margin: 4px 0;"><span style="color:#a855f7; font-weight:bold;">OMNIS ENGINE</span><br>Chaos: ${omnisFaction.chaos}% | Crime: ${omnisFaction.crime}%<br>Well-being: ${omnisFaction.physical}%`;
          
          // Wait a tiny fraction of a second for Azgaar's native tooltip logic to finish writing, then append ours.
          setTimeout(() => {
            if (!tooltip.innerHTML.includes("OMNIS ENGINE")) {
               tooltip.innerHTML += omnisHtml;
            }
          }, 10);
        }
      }
    }
  }, true);

  btnSync.addEventListener("click", async () => {
    btnSync.innerText = "Syncing...";
    
    if (!window.pack || !window.pack.cells) {
      alert("Azgaar map data not found! Please generate a map first.");
      btnSync.innerText = "📥 Sync Map to Python";
      return;
    }

    try {
      // Convert typed arrays to standard arrays to stringify correctly
      const cells = [];
      const numCells = window.pack.cells.i.length;
      for (let i = 0; i < numCells; i++) {
          if (i === 0) continue; // skip neutral 0
          cells.push({
             id: window.pack.cells.i[i],
             biome: window.pack.cells.biome[i],
             state: window.pack.cells.state[i],
             neighbors: Array.from(window.pack.cells.c[i] || []),
             x: window.pack.cells.p[i][0],
             y: window.pack.cells.p[i][1]
          });
      }

      const exportData = {
        states: window.pack.states.map(s => ({
          id: s.i,
          name: s.name,
          cells: Array.from(s.cells || [])
        })).filter(s => s.i > 0), // Filter out neutral state 0
        burgs: window.pack.burgs.map(b => ({
          id: b.i,
          name: b.name,
          state: b.state,
          population: b.population,
          x: b.x,
          y: b.y
        })).filter(b => b.i > 0),
        cells: cells
      };

      console.log("Extracting Azgaar map...", exportData);
      
      const response = await fetch("http://localhost:8000/api/map/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ azgaar_data: exportData })
      });
      
      if (response.ok) {
         alert("Synced " + exportData.states.length + " Factions and " + exportData.burgs.length + " Settlements to Omnis Backend!");
         await fetchAndApplySimState();
      } else {
         alert("Backend rejected the sync.");
      }
    } catch (e) {
      console.error(e);
      alert("Failed to sync.");
    }
    
    btnSync.innerText = "📥 Sync Map to Python";
  });

  const btnChaos = document.getElementById("btn-chaos");
  
  btnChaos.addEventListener("click", () => {
    if (!window.pack || !window.pack.cells) {
      alert("Azgaar map not initialized!");
      return;
    }
    
    console.log("OMNIS: Searing Chaos Spiral onto the map...");
    const cells = window.pack.cells;
    const width = document.getElementById("map").clientWidth || 1920;
    const height = document.getElementById("map").clientHeight || 1080;
    
    const centerX = width / 2;
    const centerY = height / 2;
    
    // Create a custom SVG group for the visual spiral if it doesn't exist
    let chaosLayer = document.getElementById("omnis-chaos-layer");
    if (!chaosLayer) {
      chaosLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
      chaosLayer.id = "omnis-chaos-layer";
      document.getElementById("map").appendChild(chaosLayer);
    }
    chaosLayer.innerHTML = ""; // Clear old spiral
    
    // Icosahedron Projection Math (12 Anchors)
    const anchors = [];
    
    // Poles
    anchors.push({ x: width / 2, y: 20 }); // North Pole (slightly offset from absolute top to be visible)
    anchors.push({ x: width / 2, y: height - 20 }); // South Pole
    
    // 5 Upper Row Anchors (Latitude ~26.5 deg)
    for (let i = 0; i < 5; i++) {
       anchors.push({ x: width * (0.1 + i * 0.2), y: height * 0.35 });
    }
    
    // 5 Lower Row Anchors (Offset by 36 deg, Latitude ~-26.5 deg)
    for (let i = 0; i < 5; i++) {
       anchors.push({ x: width * (0.2 + i * 0.2), y: height * 0.65 });
    }
    
    // Draw curved paths from each anchor to the center
    anchors.forEach((anchor, index) => {
      // 1. Draw the Anchor Diamond
      const marker = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
      marker.setAttribute("points", `${anchor.x},${anchor.y-15} ${anchor.x+10},${anchor.y} ${anchor.x},${anchor.y+15} ${anchor.x-10},${anchor.y}`);
      marker.setAttribute("fill", "#000000");
      marker.setAttribute("stroke", "#ef4444");
      marker.setAttribute("stroke-width", "2");
      chaosLayer.appendChild(marker);
      
      // 2. Calculate the curved path to the center
      const dx = centerX - anchor.x;
      const dy = centerY - anchor.y;
      
      // Midpoint
      const midX = anchor.x + dx / 2;
      const midY = anchor.y + dy / 2;
      
      // Perpendicular vector for the curve control point (Counter-clockwise curve)
      const perpX = -dy;
      const perpY = dx;
      
      // Normalize perpendicular vector
      const length = Math.sqrt(perpX * perpX + perpY * perpY);
      const curveIntensity = 150; // How drastically it curves
      const cx = midX + (perpX / length) * curveIntensity;
      const cy = midY + (perpY / length) * curveIntensity;
      
      // Draw Quadratic Bezier Curve SVG Path
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", `M ${anchor.x} ${anchor.y} Q ${cx} ${cy}, ${centerX} ${centerY}`);
      path.setAttribute("fill", "transparent");
      path.setAttribute("stroke", "#a855f7"); // Purple chaos color
      path.setAttribute("stroke-width", "4");
      path.setAttribute("stroke-dasharray", "10, 5");
      path.setAttribute("opacity", "0.7");
      
      // Animate the path drawing (optional, using CSS dash offset if we added it, but static for now)
      chaosLayer.appendChild(path);
    });
    
    // Draw the Central Eye / Convergence point
    const core = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    core.setAttribute("cx", centerX);
    core.setAttribute("cy", centerY);
    core.setAttribute("r", 20);
    core.setAttribute("fill", "#000000");
    core.setAttribute("stroke", "#a855f7");
    core.setAttribute("stroke-width", "4");
    chaosLayer.appendChild(core);
    
    alert("Icosahedron Convergence Seared! 12 Traitor Anchors placed with curved paths to the center.");
  });

  const btnLore = document.getElementById("btn-lore");
  btnLore.addEventListener("click", () => {
    if (!window.pack || !window.pack.states || !window.nameBases) {
      alert("Map not initialized. Please wait for generation to finish.");
      return;
    }
    
    // The 17 Ostraka Lore Factions
    const loreFactions = [
      "Ursine Hegemony", "River Folk", "Sump-Kin", "Iron Caladrea", "Vaneer Concord", 
      "Hive Collective", "Avians", "Flower Valwey", "Sylvian", "Sciute", 
      "Meridian Chain", "Prism Lizards", "Canopy Clans", "East Hounds", 
      "Guirrilla Clans", "Theocracy", "The Reliance"
    ];
    
    // The Lore Species for Cultures
    const loreSpecies = [
      "Ursine", "Amphibian", "Sump-Dweller", "Dwarven", "Human", 
      "Insectoid", "Avian", "Fae", "Elven", "Sciute", 
      "Merfolk", "Prism Lizard", "Simian", "Hound", 
      "Goblin", "Human", "Cyborg"
    ];
    
    // Custom Namebases for the core factions
    const customNameBases = [
      { name: "Ursine Hegemony", min: 4, max: 9, d: "", m: 0, b: "Krag,Vala,Gorn,Frost,Hearth,Bjor,Rurik,Urag,Vorn,Grendel,Thun,Snow,Ice,Peak" },
      { name: "River Folk", min: 5, max: 10, d: "", m: 0, b: "Aqual,Oa,Lura,Rivera,Tide,Flow,Stream,Lyk,Sira,Mara,Mera,Thalas,Rill,Brook" },
      { name: "Sump-Kin", min: 3, max: 8, d: "", m: 0, b: "Muck,Bog,Slime,Ooze,Drip,Murk,Grime,Fen,Mire,Sludge,Silt,Dank,Swamp" },
      { name: "Iron Caladrea", min: 5, max: 12, d: "", m: 0, b: "Iron,Forge,Steel,Anvil,Grim,Karak,Dorn,Tor,Magnus,Vol,Ignis,Smelt,Slag" },
      { name: "Vaneer Concord", min: 4, max: 10, d: "", m: 0, b: "Van,Aer,Concord,Pax,Lumina,Sol,Argent,Val,Regis,Aura,Lux,Crest" },
      { name: "Hive Collective", min: 3, max: 7, d: "", m: 0, b: "Chit,Skrek,Vesp,Nyd,Xix,Zor,Ktik,Zz,Krr,Vix,Chak,Trak,Zak" },
      { name: "Avians", min: 4, max: 10, d: "", m: 0, b: "Sky,Gale,Talon,Aerie,Soar,Wind,Corv,Aqui,Strig,Plume,Beak,Wing" },
      { name: "Flower Valwey", min: 5, max: 11, d: "", m: 0, b: "Petal,Bloom,Rose,Lily,Fern,Briar,Thistle,Spring,Nymph,Blossom,Vine,Flora" },
      { name: "Sylvian", min: 5, max: 11, d: "", m: 0, b: "Sylvan,Leaf,Oak,Elas,Tael,Vana,Lari,Thal,Ygg,Green,Root,Branch,Moss" },
      { name: "Sciute", min: 3, max: 7, d: "", m: 0, b: "Skit,Rik,Chik,Vek,Tch,Krik,Nik,Zip,Zak,Snick,Ratch,Trik,Pip" },
      { name: "Meridian Chain", min: 5, max: 10, d: "", m: 0, b: "Pearl,Reef,Tide,Wave,Coral,Deep,Salt,Shell,Cove,Abyss,Kelp,Fathom" },
      { name: "Prism Lizards", min: 4, max: 9, d: "", m: 0, b: "Scale,Sun,Bask,Glint,Shimmer,Fang,Claw,Zsk,Sss,Zath,Hiss,Viss" },
      { name: "Canopy Clans", min: 3, max: 8, d: "", m: 0, b: "Bark,Vine,Swing,Howl,Kong,Mac,Gib,Tars,Chimp,Branch,Leaf,Ape" },
      { name: "East Hounds", min: 4, max: 9, d: "", m: 0, b: "Bark,Snarl,Fang,Pack,Wolf,Lycan,Howl,Lupo,Canis,Bite,Growl,Claw" },
      { name: "Guirrilla Clans", min: 3, max: 7, d: "", m: 0, b: "Grot,Snag,Gob,Muck,Scab,Wart,Runt,Grub,Slop,Snot,Git,Stab" },
      { name: "Theocracy", min: 5, max: 12, d: "", m: 0, b: "Saint,Holy,Cross,Faith,Grace,Divine,Light,Shrine,Sanct,Pious,Chapel,Altar" },
      { name: "The Reliance", min: 3, max: 9, d: "", m: 0, b: "Cog,Gear,Wire,Spark,Iron,Tech,Mech,Synth,Volt,Flux,Grid,Node,Bot" }
    ];
    
    // Inject Custom Namebases
    customNameBases.forEach(nb => {
      window.nameBases.push(nb);
    });
    
    let baseIndex = window.nameBases.length - customNameBases.length;
    
    // Inject Factions (States)
    let factionIndex = 0;
    window.pack.states.forEach(state => {
      if (state.i === 0) return; // Skip neutral
      state.name = loreFactions[factionIndex % loreFactions.length];
      
      // Assign custom namebase if one exists for this faction
      const nbIndex = window.nameBases.findIndex(n => n.name === state.name);
      if (nbIndex !== -1) {
          state.kinship = nbIndex;
      }
      factionIndex++;
    });
    
    // Inject Species (Cultures)
    let speciesIndex = 0;
    window.pack.cultures.forEach(culture => {
      if (culture.i === 0) return; // Skip wildlands
      culture.name = loreSpecies[speciesIndex % loreSpecies.length];
      const nbIndex = window.nameBases.findIndex(n => n.name === loreFactions[speciesIndex % loreFactions.length]);
      if (nbIndex !== -1) {
          culture.base = nbIndex;
      }
      speciesIndex++;
    });
    
    // Force a UI refresh on the menus if they are open
    if (window.customization === 1) {
       document.getElementById("map").click(); // Trigger generic click to update some bindings
    }
    
    alert("🧬 Ostraka Lore Injected! Random Factions and Cultures have been overwritten with official Lore data and Linguistic Namebases.");
  });

  btnTick.addEventListener("click", async () => {
    try {
      // 1. Run the tick on the backend
      await fetch("http://localhost:8000/api/tick", { method: "POST" });
      console.log("Tick executed.");
      // 2. Immediately update the frontend to reflect the tick
      await fetchAndApplySimState();
    } catch (e) {
      console.error(e);
      alert("Tick failed. Backend offline?");
    }
  });

  btnAuto.addEventListener("click", () => {
    if (autoTickInterval) {
      clearInterval(autoTickInterval);
      autoTickInterval = null;
      btnAuto.innerText = "Auto-Tick: OFF";
      btnAuto.style.background = "rgba(239, 68, 68, 0.2)";
      btnAuto.style.borderColor = "rgba(239, 68, 68, 0.5)";
      btnAuto.style.color = "#f87171";
      statusText.innerText = "Standing By";
    } else {
      autoTickInterval = setInterval(async () => {
        try {
          await fetch("http://localhost:8000/api/tick", { method: "POST" });
          await fetchAndApplySimState(); // Auto-sync UI during auto-tick
        } catch(e) {
          console.error(e);
        }
      }, 5000); // Ticks and syncs every 5 seconds
      
      btnAuto.innerText = "Auto-Tick: ON";
      btnAuto.style.background = "rgba(34, 197, 94, 0.2)";
      btnAuto.style.borderColor = "rgba(34, 197, 94, 0.5)";
      btnAuto.style.color = "#4ade80";
      statusText.innerText = "Simulating...";
    }
  });

})();
