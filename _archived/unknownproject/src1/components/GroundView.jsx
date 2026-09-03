import React, { useMemo, useState } from 'react'
import seedrandom from 'seedrandom'
import axios from 'axios'
import { 
  Shield, Sparkles, Eye, X, Flame, PlusCircle, User, 
  Settings, Award, BookOpen, Clipboard, Check 
} from 'lucide-react'

// Base URL for FastAPI Backend Integration
const API_BASE = "http://localhost:8000/api"

// Faction HSL color mapper to match Leaflet map signatures
const getFactionHexColor = (factionId) => {
  switch (factionId) {
    case 'Heartland_Alliance':
      return '#3b82f6' // Alliance Blue
    case 'Ursine_Hegemony':
      return '#22c55e' // Hegemony Green
    case 'Aetheric_Enclave':
      return '#a855f7' // Enclave Purple
    case 'Wildlands_Tribes':
      return '#f97316' // Tribes Orange
    default:
      return '#64748b' // Slate Wilderness Gray
  }
}

export default function GroundView({ selectedHex, deepHexData, onClose, onRefresh }) {
  const { elevation, moisture, faction_id, stockpiles } = selectedHex
  const factionColor = getFactionHexColor(faction_id)

  const gridSize = 20
  const hexSeed = selectedHex.hex_id || selectedHex.properties?.hex_id || "default_seed"

  // Component local states
  const [heroForm, setHeroForm] = useState({
    name: '',
    biological_type: 'Bear',
    profession: 'Fighter',
    traits: 'Brave'
  })
  const [selectedHero, setSelectedHero] = useState(null)
  const [chronicleMarkdown, setChronicleMarkdown] = useState(null)
  const [copied, setCopied] = useState(false)
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  // Extract semantic local_scars parameters (Delta Override Pattern)
  const localScars = useMemo(() => {
    return selectedHex.local_scars || selectedHex.properties?.local_scars || {}
  }, [selectedHex])

  const ruins = useMemo(() => {
    return localScars.ruins || []
  }, [localScars])

  const isScorched = localScars.terrain_damage === "burned"

  // 1. Procedural Biome Classification
  const biome = useMemo(() => {
    if (elevation >= 0.7) return 'mountain'
    if (moisture >= 0.7) return 'swamp'
    if (moisture >= 0.4) return 'forest'
    if (moisture >= 0.2) return 'grassland'
    return 'desert'
  }, [elevation, moisture])

  // 2. Deterministic central building coordinates using hex ID seed
  const buildingsLayout = useMemo(() => {
    const rng = seedrandom(hexSeed + "_buildings")
    
    // Pick locations near center that won't overlap
    const siloX = 7 + Math.floor(rng() * 2)
    const siloY = 7 + Math.floor(rng() * 2)

    const lumberX = 11 + Math.floor(rng() * 2)
    const lumberY = 7 + Math.floor(rng() * 2)

    const barracksX = 7 + Math.floor(rng() * 2)
    const barracksY = 11 + Math.floor(rng() * 2)

    return {
      silo: { x: siloX, y: siloY },
      lumber: { x: lumberX, y: lumberY },
      barracks: { x: barracksX, y: barracksY }
    }
  }, [hexSeed])

  // 3. Procedurally Generate 20x20 Grid Cells with seedrandom
  const gridCells = useMemo(() => {
    const rng = seedrandom(hexSeed + "_terrain")
    const cells = []

    for (let y = 0; y < gridSize; y++) {
      for (let x = 0; x < gridSize; x++) {
        const isEdge = x === 0 || x === gridSize - 1 || y === 0 || y === gridSize - 1
        let type = 'ground'
        let subType = 'grass'
        let content = null // For trees, rocks, shrubs, etc.

        // Determine ground color class & details
        if (biome === 'mountain') {
          subType = 'stone'
          if (isEdge && rng() > 0.4) {
            content = 'rock'
          } else if (rng() > 0.95) {
            content = 'rock'
          }
        } else if (biome === 'swamp') {
          subType = 'mud'
          if (isEdge && rng() > 0.3) {
            content = 'dead_tree'
          } else if (rng() > 0.92) {
            content = 'water_puddle'
          }
        } else if (biome === 'forest') {
          subType = 'lush'
          if (isEdge && rng() > 0.2) {
            content = 'pine_tree'
          } else if (rng() > 0.9) {
            content = 'pine_tree'
          }
        } else if (biome === 'grassland') {
          subType = 'grass'
          if (isEdge && rng() > 0.7) {
            content = 'bush'
          } else if (rng() > 0.95) {
            content = 'flower'
          }
        } else {
          subType = 'sand'
          if (isEdge && rng() > 0.7) {
            content = 'cactus'
          } else if (rng() > 0.97) {
            content = 'dune'
          }
        }

        // Apply Delta Override: Scorched Earth / Ash overrides grass & lush mud tiles
        if (isScorched && (subType === 'grass' || subType === 'lush' || subType === 'mud')) {
          subType = 'scorched'
          if (rng() > 0.95) {
            content = 'ash_smoke'
          }
        }

        // Reserve Center Area from receiving random vegetation
        const inCenterRange = x >= 6 && x <= 13 && y >= 6 && y <= 13
        if (inCenterRange) {
          content = null
        }

        // Central Infrastructure Placements using pre-calculated seeded coordinates
        if (x === 10 && y === 10) {
          type = 'town_hall'
        } else if (stockpiles.grain > 10 && x === buildingsLayout.silo.x && y === buildingsLayout.silo.y) {
          type = 'silo'
        } else if (stockpiles.timber > 10 && x === buildingsLayout.lumber.x && y === buildingsLayout.lumber.y) {
          type = 'lumber_mill'
        } else if (stockpiles.steel > 10 && x === buildingsLayout.barracks.x && y === buildingsLayout.barracks.y) {
          type = 'barracks'
        }

        cells.push({ x, y, type, subType, content })
      }
    }
    return cells
  }, [biome, stockpiles, hexSeed, buildingsLayout, isScorched])

  // 4. Map Citizens to Absolutely Positioned Coordinates on the Grid using seedrandom
  const citizenSprites = useMemo(() => {
    if (!deepHexData || !deepHexData.local_entities) return []
    const rng = seedrandom(hexSeed + "_citizens")
    const sprites = []

    deepHexData.local_entities.forEach((cit, idx) => {
      let targetX = 10
      let targetY = 10

      // Placement based on active schedule state
      if (cit.action_state === "SLEEPING" || cit.action_state === "RESTING" || cit.action_state === "RELAXING") {
        const quarters = [
          { x: 3, y: 3 },
          { x: 3, y: 16 },
          { x: 16, y: 3 },
          { x: 16, y: 16 }
        ]
        const corner = quarters[idx % 4]
        targetX = corner.x
        targetY = corner.y
      } else if (cit.action_state === "WORKING") {
        if (stockpiles.timber > 10 && idx % 2 === 0) {
          targetX = buildingsLayout.lumber.x
          targetY = buildingsLayout.lumber.y + 1
        } else if (stockpiles.grain > 10) {
          targetX = buildingsLayout.silo.x
          targetY = buildingsLayout.silo.y + 1
        } else {
          targetX = 9
          targetY = 10
        }
      } else if (cit.action_state === "EATING" || cit.metabolic_state.hunger_level > 70) {
        if (stockpiles.grain > 10) {
          targetX = buildingsLayout.silo.x
          targetY = buildingsLayout.silo.y - 1
        } else {
          targetX = 10
          targetY = 9
        }
      } else if (cit.action_state === "PRAYING") {
        targetX = 10
        targetY = 12
      } else {
        targetX = 4 + Math.floor(rng() * 12)
        targetY = 4 + Math.floor(rng() * 12)
      }

      const offsetX = (rng() - 0.5) * 0.5
      const offsetY = (rng() - 0.5) * 0.5

      sprites.push({
        citizen: cit,
        gridX: targetX + offsetX,
        gridY: targetY + offsetY
      })
    })

    return sprites
  }, [deepHexData, stockpiles, hexSeed, buildingsLayout])

  // Extract hero list from local entities
  const heroEntities = useMemo(() => {
    if (!deepHexData || !deepHexData.local_entities) return []
    return deepHexData.local_entities.filter(ent => ent.is_hero === true)
  }, [deepHexData])

  // Handle Hero Injection API call
  const handleSummonHero = async (e) => {
    e.preventDefault()
    if (!heroForm.name.trim()) return
    
    setLoading(true)
    setSuccessMessage('')
    try {
      const res = await axios.post(`${API_BASE}/hex/${selectedHex.hex_id}/hero`, {
        name: heroForm.name,
        biological_type: heroForm.biological_type,
        profession: heroForm.profession,
        traits: heroForm.traits
      })
      
      setSuccessMessage(`Summoned Hero ${res.data.hero.name}!`)
      setHeroForm({
        name: '',
        biological_type: 'Bear',
        profession: 'Fighter',
        traits: 'Brave'
      })
      
      if (onRefresh) onRefresh()
    } catch (err) {
      console.error("Failed to summon hero:", err)
    } finally {
      setLoading(false)
    }
  }

  // Handle changing hero active directive override
  const handleHeroDirectiveChange = async (heroId, directive) => {
    try {
      await axios.put(`${API_BASE}/hex/${selectedHex.hex_id}/entity/${heroId}/directive`, {
        directive: directive
      })
      
      if (onRefresh) onRefresh()
      
      // Update selected hero locally to show instant feedback
      setSelectedHero(prev => {
        if (prev && prev.entity_id === heroId) {
          return { ...prev, active_directive: directive }
        }
        return prev
      })
    } catch (err) {
      console.error("Failed to override hero directive:", err)
    }
  }

  // Export Obsidian Chronicle Markdown from Novelist's Loom API
  const handleExportChronicle = async (heroId) => {
    setLoading(true)
    setCopied(false)
    try {
      const res = await axios.get(`${API_BASE}/export/chronicle`, {
        params: { hero_id: heroId }
      })
      setChronicleMarkdown(res.data.markdown_content)
    } catch (err) {
      console.error("Failed to export chronicle:", err)
    } finally {
      setLoading(false)
    }
  }

  // Copy chronicle markdown to clipboard
  const handleCopyToClipboard = () => {
    if (!chronicleMarkdown) return
    navigator.clipboard.writeText(chronicleMarkdown)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Helper to color code citizen sprites
  const getCitizenColor = (biologicalType) => {
    switch (biologicalType) {
      case 'Bear':
        return '#854d0e' // Rich Brown
      case 'Wolf':
        return '#1e3a8a' // Dark Blue
      case 'Mouse':
        return '#94a3b8' // Slate Grey
      default:
        return '#cbd5e1'
    }
  }

  // Get tile visual class/content (supporting Delta Override ruined parameters)
  const renderTileContent = (cell) => {
    if (cell.type === 'town_hall') {
      const isRuined = ruins.includes("town_hall") || ruins.includes("lumber_mill") && ruins.includes("silo") && ruins.includes("barracks")
      return (
        <div 
          className={`w-full h-full border-2 border-white/20 rounded flex items-center justify-center font-bold text-[10px] text-white shadow-lg ${isRuined ? 'animate-pulse bg-red-950/80 border-red-800' : 'animate-pulse'}`}
          style={{ backgroundColor: isRuined ? '#450a0a' : factionColor }}
        >
          {isRuined ? '🏚️🔥' : '🏰'}
        </div>
      )
    }
    if (cell.type === 'silo') {
      const isRuined = ruins.includes("silo")
      return (
        <div className={`w-full h-full border rounded flex items-center justify-center text-xs shadow-md transition duration-300 ${
          isRuined ? 'bg-[#292524] border-red-950/80 animate-pulse text-[10px]' : 'bg-[#4a5568] border-[#2d3748]'
        }`}>
          {isRuined ? '🏚️🌾' : '🌾'}
        </div>
      )
    }
    if (cell.type === 'lumber_mill') {
      const isRuined = ruins.includes("lumber_mill")
      return (
        <div className={`w-full h-full border rounded flex items-center justify-center text-xs shadow-md transition duration-300 ${
          isRuined ? 'bg-[#292524] border-red-950/80 animate-pulse text-[10px]' : 'bg-[#8b5a2b] border-[#5c4033]'
        }`}>
          {isRuined ? '🏚️🪓' : '🪓'}
        </div>
      )
    }
    if (cell.type === 'barracks') {
      const isRuined = ruins.includes("barracks")
      return (
        <div className={`w-full h-full border-2 rounded flex items-center justify-center text-xs shadow-md transition duration-300 ${
          isRuined ? 'bg-[#292524] border-red-950/80 animate-pulse text-[10px]' : 'bg-[#1e293b] border-red-950'
        }`}>
          {isRuined ? '🏚️🛡️' : '🛡️'}
        </div>
      )
    }

    switch (cell.content) {
      case 'pine_tree':
        return <span className="text-sm select-none">🌲</span>
      case 'dead_tree':
        return <span className="text-sm select-none">🪵</span>
      case 'rock':
        return <span className="text-xs select-none">🪨</span>
      case 'bush':
        return <span className="text-[10px] select-none">🌿</span>
      case 'flower':
        return <span className="text-[10px] select-none">🌸</span>
      case 'cactus':
        return <span className="text-xs select-none">🌵</span>
      case 'water_puddle':
        return <span className="text-xs select-none">💧</span>
      case 'ash_smoke':
        return <span className="text-[10px] select-none animate-pulse">💨</span>
      default:
        return null
    }
  }

  const getTileBgClass = (subType) => {
    switch (subType) {
      case 'stone':
        return 'bg-[#2d3748] border border-[#1a202c]/40'
      case 'mud':
        return 'bg-[#2b1d14] border border-[#1b120c]/40'
      case 'lush':
        return 'bg-[#0f2e1a] border border-[#091b0f]/40'
      case 'sand':
        return 'bg-[#66533c] border border-[#483927]/40'
      case 'scorched':
        return 'bg-[#18181b] border border-[#09090b]/40'
      default:
        return 'bg-[#183923] border border-[#102717]/40'
    }
  }

  return (
    <div className="fixed inset-0 bg-[#06080d]/99 backdrop-blur-xl z-[99999] flex flex-col md:flex-row overflow-hidden animate-fade-in font-sans">
      
      {/* Style Injection */}
      <style dangerouslySetInnerHTML={{__html: `
        .ground-grid {
          display: grid;
          grid-template-columns: repeat(20, minmax(0, 1fr));
          grid-template-rows: repeat(20, minmax(0, 1fr));
        }
        .ground-tile {
          image-rendering: pixelated;
          transition: filter 0.15s ease;
        }
        .ground-tile:hover {
          filter: brightness(1.2);
        }
        .citizen-sprite {
          transform: translate(-50%, -50%);
          box-shadow: 0 0 6px rgba(0,0,0,0.8);
          animation: spriteFloat 1.8s ease-in-out infinite alternate;
        }
        @keyframes spriteFloat {
          0% { margin-top: 0; }
          100% { margin-top: -2px; }
        }
        .retro-tooltip {
          visibility: hidden;
          opacity: 0;
          transition: opacity 0.15s ease, visibility 0.15s ease;
        }
        .citizen-dot:hover .retro-tooltip {
          visibility: visible;
          opacity: 1;
        }
      `}} />

      {/* A. 2D Retro Map Grid Viewport */}
      <div className="flex-1 relative h-[50vh] md:h-full flex items-center justify-center p-4 bg-black/40 border-r border-white/[0.04] overflow-hidden">
        
        {/* Main Grid Wrapper */}
        <div className="relative w-full max-w-[580px] aspect-square rounded-xl overflow-hidden border-4 border-slate-800 shadow-2xl bg-slate-950 flex flex-col shrink-0">
          
          <div className="ground-grid w-full h-full relative">
            {gridCells.map((cell, idx) => (
              <div 
                key={idx} 
                className={`ground-tile w-full h-full flex items-center justify-center select-none ${getTileBgClass(cell.subType)}`}
              >
                {renderTileContent(cell)}
              </div>
            ))}

            {/* Overlay Citizens sprites layer */}
            {citizenSprites.map((sprite) => {
              const cit = sprite.citizen
              const leftPercent = (sprite.gridX / gridSize) * 100
              const topPercent = (sprite.gridY / gridSize) * 100
              const citizenColor = getCitizenColor(cit.biological_type)
              
              const isHero = cit.is_hero
              const specIcon = isHero ? "👑" : (cit.biological_type === "Bear" ? "🐻" :
                              cit.biological_type === "Mouse" ? "🐭" : "🐺")

              return (
                <div 
                  key={cit.entity_id}
                  className="citizen-dot absolute w-4.5 h-4.5 rounded-full flex items-center justify-center cursor-pointer citizen-sprite"
                  style={{ 
                    left: `${leftPercent}%`, 
                    top: `${topPercent}%`, 
                    backgroundColor: isHero ? '#eab308' : citizenColor,
                    border: isHero ? '2px solid #fef08a' : '1.5px solid #fff',
                    boxShadow: isHero ? '0 0 0 2px rgba(234, 179, 8, 0.4), 0 0 10px rgba(234, 179, 8, 0.8)' : '0 0 6px rgba(0,0,0,0.8)',
                    zIndex: isHero ? 100 : 50
                  }}
                  onClick={() => {
                    if (isHero) {
                      setSelectedHero(cit)
                    }
                  }}
                >
                  <span className="text-[9px] mt-0.5">{specIcon}</span>

                  {/* Pixelated Hover Tooltip */}
                  <div className="retro-tooltip absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-48 bg-[#0b0e16]/98 border border-white/[0.12] p-3 rounded-lg shadow-2xl text-[10px] text-slate-300 z-[999] pointer-events-none flex flex-col gap-2 font-mono">
                    <div className="flex justify-between border-b border-white/[0.08] pb-1">
                      <span className="font-bold text-slate-200">{cit.entity_id.split('_').slice(-2).join('_')}</span>
                      <span className="text-[8px] font-bold text-slate-400 capitalize">{cit.profession}</span>
                    </div>
                    <div className="flex flex-col gap-1">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Class:</span>
                        <span className={`font-bold ${isHero ? 'text-yellow-400 animate-pulse' : 'text-slate-400'}`}>
                          {isHero ? "PLAYER HERO" : "CIVILIAN NPC"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Action:</span>
                        <span className="text-emerald-400 font-bold">{cit.action_state}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Sanity:</span>
                        <span className="text-cyan-400">{(cit.metabolic_state.sanity_score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Hunger:</span>
                        <span className={`font-bold ${cit.metabolic_state.hunger_level > 80 ? 'text-red-400 animate-pulse' : 'text-slate-300'}`}>
                          {cit.metabolic_state.hunger_level}%
                        </span>
                      </div>
                    </div>
                    <div className="border-t border-white/[0.08] pt-1 text-[8px] text-slate-500 italic">
                      "{cit.dna_profile.personality}"
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

        </div>

        {/* Back to Macro Map Trigger */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 py-2 px-3.5 bg-red-950 hover:bg-red-900 border border-red-800 text-red-200 font-bold rounded-lg text-xs transition duration-200 shadow-lg flex items-center gap-1.5 z-50 uppercase tracking-wider font-mono"
        >
          <X className="w-3.5 h-3.5" /> Back to Macro Map
        </button>
      </div>

      {/* B. Glassmorphism Diorama Sidebar Console */}
      <div className="w-full md:w-[420px] bg-[#080b11]/98 flex flex-col h-[50vh] md:h-full overflow-y-auto shrink-0 relative p-6 border-t md:border-t-0 border-white/[0.05]">
        
        {/* Region Header */}
        <div className="flex flex-col border-b border-white/[0.06] pb-4 mb-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">{selectedHex.hex_id}</h2>
            {isScorched || ruins.length > 0 ? (
              <span className="text-[10px] text-red-400 font-bold uppercase tracking-widest flex items-center gap-1">
                <Flame className="w-3 h-3 text-red-400 animate-pulse" /> Battle Scarred
              </span>
            ) : (
              <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-emerald-400 animate-pulse" /> Pristine State
              </span>
            )}
          </div>
          <h1 className="text-lg font-black text-slate-100 tracking-tight mt-1 flex items-center gap-1.5 uppercase font-mono">
            <Shield className="w-5 h-5 text-purple-500" /> RPG Ground View
          </h1>
        </div>

        {/* Console Sections */}
        <div className="flex flex-col gap-4">

          {/* 1. HERO PROTOCOL & LOOM CONTROLS */}
          <div className="bg-[#0f111a]/80 border border-yellow-500/20 p-4 rounded-xl flex flex-col gap-3 shadow-lg shadow-yellow-950/5">
            <h3 className="text-xs font-bold text-yellow-400 uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Award className="w-4 h-4 text-yellow-400 animate-pulse" /> Hero Protocol Console
            </h3>
            
            {successMessage && (
              <div className="p-2 bg-emerald-950/40 border border-emerald-800/40 rounded text-emerald-400 text-[10px] font-bold text-center font-mono">
                {successMessage}
              </div>
            )}

            {/* List of active heroes in hex */}
            {heroEntities.length > 0 ? (
              <div className="flex flex-col gap-2">
                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold font-mono">Active Heroes in Hex</span>
                <div className="flex flex-wrap gap-2">
                  {heroEntities.map(hero => (
                    <button
                      key={hero.entity_id}
                      onClick={() => setSelectedHero(hero)}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-bold font-mono transition duration-200 flex items-center gap-1.5 ${
                        selectedHero?.entity_id === hero.entity_id 
                          ? 'bg-yellow-500/20 border-yellow-400 text-yellow-200' 
                          : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.06] text-slate-300'
                      }`}
                    >
                      👑 {hero.name}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-[10px] text-slate-500 italic">No player-controlled custom heroes are currently injected into this regional grid.</p>
            )}

            {/* Selected Hero details, directive controls, and Loom export */}
            {selectedHero ? (
              <div className="bg-black/40 border border-white/[0.04] p-3 rounded-lg flex flex-col gap-3 animate-slide-up mt-1">
                <div className="flex justify-between items-start border-b border-white/[0.06] pb-2">
                  <div className="flex flex-col">
                    <span className="text-xs font-bold text-yellow-400 font-mono">👑 {selectedHero.name}</span>
                    <span className="text-[9px] text-slate-500 font-mono">{selectedHero.entity_id}</span>
                  </div>
                  <button 
                    onClick={() => setSelectedHero(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-300 font-mono">
                  <div>
                    <span className="text-slate-500">Species:</span> {selectedHero.biological_type}
                  </div>
                  <div>
                    <span className="text-slate-500">Profession:</span> {selectedHero.profession}
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-500">Traits:</span> {selectedHero.dna_profile?.personality || "Quiet"}
                  </div>
                  <div>
                    <span className="text-slate-500">Hunger:</span> <span className={selectedHero.metabolic_state.hunger_level > 80 ? 'text-red-400 font-bold' : ''}>{selectedHero.metabolic_state.hunger_level}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Sanity:</span> {(selectedHero.metabolic_state.sanity_score * 100).toFixed(0)}%
                  </div>
                </div>

                {/* Directive selector dropdown */}
                <div className="flex flex-col gap-1.5 mt-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-1">
                    <Settings className="w-3 h-3 text-yellow-400" /> Pre-Tick Directive Override
                  </label>
                  <select
                    value={selectedHero.active_directive || 'AUTO'}
                    onChange={(e) => handleHeroDirectiveChange(selectedHero.entity_id, e.target.value)}
                    className="w-full bg-[#0b0e16] border border-white/[0.08] hover:border-yellow-500/40 rounded-lg p-2 text-xs text-slate-300 font-mono focus:outline-none focus:border-yellow-400 transition"
                  >
                    <option value="AUTO">⚙️ AUTO (Follow standard schedule physics)</option>
                    <option value="SCOUT">🏹 SCOUT (Observe hex boundaries)</option>
                    <option value="HARVEST">🌾 HARVEST (Gather economic stockpiles)</option>
                    <option value="GUARD">🛡️ GUARD (Defend regional territory)</option>
                    <option value="MEDITATE">🔮 MEDITATE (Channel magic/aether flow)</option>
                  </select>
                </div>

                {/* Export Obsidian Chronicle Button */}
                <button
                  onClick={() => handleExportChronicle(selectedHero.entity_id)}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 bg-gradient-to-r from-yellow-500/20 to-amber-500/20 hover:from-yellow-500/30 hover:to-amber-500/30 border border-yellow-500/30 text-yellow-300 font-bold rounded text-xs transition duration-200 font-mono shadow-md mt-1"
                >
                  <BookOpen className="w-3.5 h-3.5 text-yellow-400" />
                  {loading ? "weaving chronicle..." : "📜 Export Obsidian Chronicle"}
                </button>
              </div>
            ) : null}

            {/* Summons circle collapsible form to create new hero */}
            <form onSubmit={handleSummonHero} className="bg-black/20 border border-white/[0.03] p-3 rounded-lg flex flex-col gap-2.5">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider font-mono flex items-center gap-1">
                <PlusCircle className="w-3.5 h-3.5 text-yellow-400" /> Summon Player Character
              </span>
              
              <div className="flex flex-col gap-1">
                <input
                  type="text"
                  placeholder="Hero Name..."
                  value={heroForm.name}
                  onChange={(e) => setHeroForm(prev => ({ ...prev, name: e.target.value }))}
                  required
                  className="bg-[#0b0e16] border border-white/[0.08] rounded p-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-yellow-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-0.5">
                  <label className="text-[8px] text-slate-500 font-bold uppercase font-mono">Species</label>
                  <select
                    value={heroForm.biological_type}
                    onChange={(e) => setHeroForm(prev => ({ ...prev, biological_type: e.target.value }))}
                    className="bg-[#0b0e16] border border-white/[0.08] rounded p-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-yellow-400"
                  >
                    <option value="Bear">🐻 Bear</option>
                    <option value="Mouse">🐭 Mouse</option>
                    <option value="Wolf">🐺 Wolf</option>
                  </select>
                </div>

                <div className="flex flex-col gap-0.5">
                  <label className="text-[8px] text-slate-500 font-bold uppercase font-mono">Profession</label>
                  <input
                    type="text"
                    placeholder="e.g. Fighter"
                    value={heroForm.profession}
                    onChange={(e) => setHeroForm(prev => ({ ...prev, profession: e.target.value }))}
                    required
                    className="bg-[#0b0e16] border border-white/[0.08] rounded p-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-yellow-400"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-0.5">
                <label className="text-[8px] text-slate-500 font-bold uppercase font-mono">Traits (DNA Personality)</label>
                <input
                  type="text"
                  placeholder="e.g. Brave, Greedy"
                  value={heroForm.traits}
                  onChange={(e) => setHeroForm(prev => ({ ...prev, traits: e.target.value }))}
                  required
                  className="bg-[#0b0e16] border border-white/[0.08] rounded p-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-yellow-400"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-1.5 py-1.5 px-3 bg-gradient-to-r from-yellow-600 to-amber-600 hover:brightness-110 text-white font-bold rounded text-xs transition duration-200 shadow-md shadow-yellow-950/20 flex items-center justify-center gap-1 uppercase font-mono tracking-wider"
              >
                <Sparkles className="w-3.5 h-3.5" /> Summon Hero
              </button>
            </form>
          </div>

          {/* Active Environmental Scars (Level 2.5 Delta overrides feedback) */}
          {(isScorched || ruins.length > 0) && (
            <div className="bg-red-950/20 border border-red-800/40 p-4 rounded-xl flex flex-col gap-2">
              <h3 className="text-[10px] font-bold text-red-400 uppercase tracking-widest flex items-center gap-1">
                ⚠️ Permanent Scars Detected
              </h3>
              <div className="text-xs text-slate-300 flex flex-col gap-1.5 mt-1 font-mono">
                {isScorched && (
                  <div className="flex justify-between">
                    <span className="text-red-400">Scorched Earth:</span>
                    <span className="text-slate-400">ACTIVE (Ash)</span>
                  </div>
                )}
                {ruins.length > 0 && (
                  <div className="flex flex-col gap-1">
                    <span className="text-red-400">Ruined Structures:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {ruins.map(b => (
                        <span key={b} className="text-[9px] px-1.5 py-0.5 bg-red-950 border border-red-800 text-red-300 rounded uppercase">
                          {b.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Map Overview details */}
          <div className="bg-white/[0.015] border border-white/[0.04] p-4 rounded-xl flex flex-col gap-3">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1">
              <Eye className="w-3.5 h-3.5 text-purple-400" /> Region Details
            </h3>
            
            <div className="flex flex-col gap-2.5 text-xs text-slate-300">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-[#854d0e] border border-white/20" /> Bear Citizens
                </span>
                <span className="font-mono text-slate-400 font-semibold">{selectedHex.demographics.Bears || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-[#1e3a8a] border border-white/20" /> Wolf Citizens
                </span>
                <span className="font-mono text-slate-400 font-semibold">{selectedHex.demographics.Wolves || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-[#94a3b8] border border-white/20" /> Mouse Citizens
                </span>
                <span className="font-mono text-slate-400 font-semibold">{selectedHex.demographics.Mice || 0}</span>
              </div>
              
              <div className="border-t border-white/[0.04] pt-2.5 mt-0.5 flex flex-col gap-2.5">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    🏰 Faction Control
                  </span>
                  <span className="font-semibold text-slate-300 capitalize font-mono" style={{ color: factionColor }}>
                    {selectedHex.faction_id ? selectedHex.faction_id.replace('_', ' ') : "Neutral Wilderness"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    🌾 Grain Silo
                  </span>
                  <span className="font-semibold text-slate-400">
                    {stockpiles.grain > 10 
                      ? (ruins.includes("silo") ? "💥 Ruined (Rubble)" : `Rendered (${buildingsLayout.silo.x}, ${buildingsLayout.silo.y})`) 
                      : "0 (Low Stock)"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    🪓 Lumber Mill
                  </span>
                  <span className="font-semibold text-slate-400">
                    {stockpiles.timber > 10 
                      ? (ruins.includes("lumber_mill") ? "💥 Ruined (Rubble)" : `Rendered (${buildingsLayout.lumber.x}, ${buildingsLayout.lumber.y})`) 
                      : "0 (Low Stock)"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    🛡️ Weapons Barracks
                  </span>
                  <span className="font-semibold text-slate-400">
                    {stockpiles.steel > 10 
                      ? (ruins.includes("barracks") ? "💥 Ruined (Rubble)" : `Rendered (${buildingsLayout.barracks.x}, ${buildingsLayout.barracks.y})`) 
                      : "0 (Low Stock)"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Environmental metrics */}
          <div className="bg-white/[0.01] border border-white/[0.03] p-4 rounded-xl flex flex-col gap-2.5 text-xs text-slate-400">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Procedural Geography</h3>
            <div className="flex justify-between mt-1">
              <span>Classified Biome:</span>
              <span className="text-slate-300 font-semibold uppercase font-mono">{biome}</span>
            </div>
            <div className="flex justify-between">
              <span>Elevation Metric:</span>
              <span className="text-slate-300 font-semibold font-mono">{(elevation * 1000).toFixed(0)}m</span>
            </div>
            <div className="flex justify-between">
              <span>Moisture Rating:</span>
              <span className="text-slate-300 font-semibold font-mono">{(moisture * 100).toFixed(0)}%</span>
            </div>
          </div>

        </div>

      </div>

      {/* C. NOVELIST'S LOOM EXPORT MODAL */}
      {chronicleMarkdown && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-[99999] flex items-center justify-center p-4">
          <div className="bg-[#0b0e16]/98 border border-yellow-500/30 p-8 rounded-2xl max-w-2xl w-full shadow-2xl relative flex flex-col gap-5 animate-slide-up max-h-[85vh] overflow-hidden">
            
            {/* Header */}
            <div className="flex justify-between items-center border-b border-white/[0.06] pb-4 shrink-0">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-yellow-400" />
                <h2 className="text-md font-bold text-slate-100 font-mono tracking-wide uppercase">Novelist's Loom Chronicle Export</h2>
              </div>
              <button
                onClick={() => setChronicleMarkdown(null)}
                className="p-1 rounded-full bg-white/[0.02] hover:bg-white/[0.08] text-slate-400 hover:text-white transition border border-white/[0.05]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Scrollable Markdown Content Area */}
            <div className="flex-1 overflow-y-auto bg-black/40 border border-white/[0.05] p-5 rounded-xl font-mono text-[11px] text-slate-300 leading-relaxed max-h-[50vh] whitespace-pre-wrap select-text">
              {chronicleMarkdown}
            </div>

            {/* Actions Footer */}
            <div className="flex gap-3 shrink-0 pt-2">
              <button
                onClick={handleCopyToClipboard}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 px-4 bg-gradient-to-r from-yellow-600 to-amber-600 hover:brightness-110 text-white font-bold rounded-lg text-xs transition uppercase font-mono tracking-wider shadow-lg"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-200" /> : <Clipboard className="w-4 h-4" />}
                {copied ? "Copied to Clipboard!" : "Copy to Clipboard"}
              </button>
              <button
                onClick={() => setChronicleMarkdown(null)}
                className="py-2.5 px-6 bg-slate-900 hover:bg-slate-800 border border-white/[0.08] text-slate-300 font-bold rounded-lg text-xs transition uppercase font-mono tracking-wider"
              >
                Dismiss
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  )
}
