import React, { useState, useEffect } from 'react'
import { 
  X, BookOpen, RefreshCw, AlertCircle, Calendar, Eye, Users, 
  MapPin, Heart, ShieldAlert, Sparkles, Filter, Search 
} from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://localhost:8000/api"

export default function ChronicleLog({ onClose }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Search & Filter state
  const [selectedEventFilter, setSelectedEventFilter] = useState("")
  const [searchHex, setSearchHex] = useState("")
  
  // TTRPG Inspect Survivors state
  const [inspectEvent, setInspectEvent] = useState(null)

  useEffect(() => {
    fetchLogs()
  }, [selectedEventFilter, searchHex])

  const fetchLogs = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {}
      if (selectedEventFilter) params.event_type = selectedEventFilter
      if (searchHex) params.hex_id = searchHex

      const res = await axios.get(`${API_BASE}/logs`, { params })
      setLogs(res.data)
    } catch (err) {
      console.error("Failed to load chronicle logs:", err)
      setError("Failed to fetch historical chronicles from active PostgreSQL logs database.")
    } finally {
      setLoading(false)
    }
  }

  // Helper to format tick count to fantasy world-time Year/Day
  const formatTickTime = (tick) => {
    const hoursPerDay = 24
    const daysPerYear = 365
    
    const totalDays = Math.floor(tick / hoursPerDay)
    const year = Math.floor(totalDays / daysPerYear) + 1
    const day = (totalDays % daysPerYear) + 1
    const hour = tick % hoursPerDay
    
    return `Year ${year}, Day ${day} (${String(hour).padStart(2, '0')}:00)`
  }

  // Get color tags for event types
  const getEventBadgeClass = (type) => {
    switch (type.toUpperCase()) {
      case 'SIEGE':
        return 'bg-red-500/10 text-red-400 border-red-500/20'
      case 'STORM':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20'
      case 'FAMINE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
      case 'REBELLION':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }
  }

  // Get Event Emojis
  const getEventEmoji = (type) => {
    switch (type.toUpperCase()) {
      case 'SIEGE': return '⚔️'
      case 'STORM': return '🌀'
      case 'FAMINE': return '🌾'
      case 'REBELLION': return '✊'
      default: return '📜'
    }
  }

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-[9999] flex items-center justify-center p-4">
      <div className="bg-[#0b0e16]/95 border border-white/[0.08] rounded-2xl max-w-2xl w-full shadow-2xl relative flex flex-col h-[85vh] overflow-hidden animate-slide-up">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-full bg-white/[0.02] hover:bg-white/[0.08] text-slate-400 hover:text-white transition border border-white/[0.05]"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Panel Header */}
        <div className="p-6 border-b border-white/[0.06] bg-white/[0.01] flex items-center gap-3">
          <div className="p-2 bg-pink-500/10 border border-pink-500/20 rounded-lg">
            <BookOpen className="w-5 h-5 text-pink-400" />
          </div>
          <div>
            <h2 className="text-md font-bold text-slate-100 uppercase tracking-wider font-mono">Ostraka Chronicle</h2>
            <p className="text-[11px] text-slate-400 mt-0.5 uppercase tracking-widest font-medium">Historical Timeline & Story Generator Feed</p>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="px-6 py-4 border-b border-white/[0.04] bg-white/[0.005] flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>Event type:</span>
            <select 
              value={selectedEventFilter}
              onChange={(e) => setSelectedEventFilter(e.target.value)}
              className="bg-[#0e111a] border border-white/[0.06] rounded px-2.5 py-1 text-slate-300 outline-none font-semibold focus:border-pink-500/50 transition cursor-pointer"
            >
              <option value="">ALL EVENTS</option>
              <option value="SIEGE">SIEGE</option>
              <option value="FAMINE">FAMINE</option>
              <option value="STORM">STORM</option>
              <option value="REBELLION">REBELLION</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-[#0e111a] border border-white/[0.06] rounded px-2.5 py-1 max-w-[200px] w-full">
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <input 
              type="text"
              placeholder="Search Hex ID..."
              value={searchHex}
              onChange={(e) => setSearchHex(e.target.value)}
              className="bg-transparent border-none outline-none text-xs text-slate-300 placeholder-slate-600 w-full"
            />
          </div>
        </div>

        {/* Logs Timeline Timeline */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin text-pink-400" />
              <span>Translating Chronosphere records...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-950/30 border border-red-800/40 rounded-xl text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : logs.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center gap-2 justify-center border border-dashed border-white/[0.05] rounded-2xl bg-white/[0.002]">
              <Calendar className="w-8 h-8 text-slate-700 animate-pulse" />
              <span>No historical events have occurred matching this filter query.</span>
            </div>
          ) : (
            <div className="flex flex-col gap-4 pl-4 relative border-l border-white/[0.04] ml-2">
              {logs.map((log) => {
                const badgeClass = getEventBadgeClass(log.event_type)
                const emoji = getEventEmoji(log.event_type)
                const hasSnapshot = log.deep_snapshot && log.deep_snapshot.length > 0

                return (
                  <div key={log.id} className="relative flex flex-col gap-2 bg-white/[0.015] border border-white/[0.04] rounded-xl p-4 hover:border-pink-500/10 hover:bg-white/[0.025] transition duration-200 shadow-sm">
                    {/* Time dot indicator */}
                    <div className={`absolute -left-[27px] top-[18px] w-3 h-3 rounded-full border border-[#0b0e16] flex items-center justify-center ${
                      log.event_type === 'SIEGE' ? 'bg-red-500' :
                      log.event_type === 'STORM' ? 'bg-purple-500' :
                      log.event_type === 'FAMINE' ? 'bg-amber-500' : 'bg-cyan-500'
                    }`}></div>

                    {/* Timeline Log Row Header */}
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex flex-col">
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1 font-mono">
                          <Calendar className="w-3 h-3 text-pink-400" />
                          {formatTickTime(log.tick_count)}
                        </span>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className={`badge ${badgeClass} border font-bold text-[10px] py-0.5 px-2`}>
                            {emoji} {log.event_type}
                          </span>
                          <span className="text-[10px] bg-white/[0.02] border border-white/[0.06] rounded px-1.5 py-0.5 text-slate-400 font-bold font-mono uppercase flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5" />
                            {log.hex_id}
                          </span>
                        </div>
                      </div>

                      {/* Severity indicator */}
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                        log.severity >= 4 ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-white/[0.02] text-slate-400 border border-white/[0.06]'
                      }`}>
                        SEVERITY {log.severity}/5
                      </span>
                    </div>

                    {/* Summary Description */}
                    <p className="text-xs text-slate-300 font-medium leading-relaxed mt-1 font-serif bg-black/10 border border-white/[0.01] p-3 rounded-lg">
                      {log.summary}
                    </p>

                    {/* TTRPG Encounter Hook Snapshot Button */}
                    {hasSnapshot && (
                      <div className="flex justify-end mt-2">
                        <button 
                          onClick={() => setInspectEvent(log)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-gradient-to-r from-pink-600/20 to-purple-600/20 border border-pink-500/30 hover:border-pink-500/60 text-pink-300 font-bold uppercase rounded text-[9px] tracking-wider transition hover:brightness-110 shadow-md shadow-pink-950/20"
                        >
                          <Users className="w-3.5 h-3.5" />
                          Inspect Survivors ({log.deep_snapshot.length})
                        </button>
                      </div>
                    )}

                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/[0.06] bg-white/[0.015] flex justify-end">
          <button 
            onClick={onClose}
            className="w-full py-2.5 px-4 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-bold rounded-lg text-xs transition duration-200 hover:brightness-110 shadow-lg shadow-pink-950/30"
          >
            Close Feed
          </button>
        </div>

      </div>

      {/* TTRPG SURVIVORS INSPECTOR SUB-MODAL */}
      {inspectEvent && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-[10000] flex items-center justify-center p-4">
          <div className="bg-[#0b0e16]/95 border border-white/[0.08] rounded-2xl max-w-xl w-full shadow-2xl relative flex flex-col max-h-[80vh] overflow-hidden animate-slide-up">
            
            <button 
              onClick={() => setInspectEvent(null)}
              className="absolute top-4 right-4 p-1.5 rounded-full bg-white/[0.02] hover:bg-white/[0.08] text-slate-400 hover:text-white transition border border-white/[0.05]"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Sub-Header */}
            <div className="p-6 border-b border-white/[0.06] bg-white/[0.01] flex items-center gap-3">
              <div className="p-2 bg-pink-500/10 border border-pink-500/20 rounded-lg">
                <Users className="w-5 h-5 text-pink-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider font-mono">TTRPG Encounter Hook: Incident Survivors</h3>
                <p className="text-[10px] text-slate-400 mt-0.5 uppercase tracking-widest font-medium">NPC Snapshots from Hex {inspectEvent.hex_id} • Tick {inspectEvent.tick_count}</p>
              </div>
            </div>

            {/* Survivors Grid */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
              <div className="p-3 bg-white/[0.015] border border-white/[0.04] rounded-xl flex items-start gap-2.5">
                <ShieldAlert className="w-4 h-4 text-pink-400 shrink-0 mt-0.5" />
                <span className="text-[10px] text-slate-400 leading-normal">
                  Below are the dynamic high-fidelity citizens that survived this exact historical event. Use their traits, stats, and fears as immediate encounter elements for your ongoing fantasy tabletop campaign!
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
                {inspectEvent.deep_snapshot.map((npc, idx) => {
                  const specIcon = npc.biological_type === "Bear" ? "🐻" :
                                  npc.biological_type === "Mouse" ? "🐭" : "🐺"
                  const health = npc.metabolic_state?.health ?? 100
                  const hunger = npc.metabolic_state?.hunger_level ?? 0
                  const sanity = npc.metabolic_state?.sanity_score ?? 1.0

                  return (
                    <div key={idx} className="bg-white/[0.015] border border-white/[0.05] rounded-xl p-3.5 hover:border-pink-500/10 transition flex flex-col gap-2">
                      
                      {/* Name Profession & Bio */}
                      <div className="flex justify-between items-start gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{specIcon}</span>
                          <div className="flex flex-col">
                            <span className="text-[11px] font-mono font-bold text-slate-200">{npc.entity_id.split('_').slice(-2).join('_')}</span>
                            <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold capitalize">{npc.profession}</span>
                          </div>
                        </div>
                        <span className="text-[9px] font-bold text-slate-400 bg-white/[0.03] border border-white/[0.06] rounded px-1.5 py-0.5 font-mono">
                          {npc.action_state}
                        </span>
                      </div>

                      {/* DNA Core parameters */}
                      <div className="text-[10px] text-slate-400 flex flex-col gap-1 mt-1 bg-black/15 p-2 rounded">
                        <div className="flex justify-between">
                          <span>Personality</span>
                          <span className="text-slate-300 font-bold">{npc.dna_profile?.personality || "DISCIPLINED"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Core Interest</span>
                          <span className="text-slate-300 font-bold">{npc.dna_profile?.interest || "MILITARY"}</span>
                        </div>
                        <div className="flex justify-between text-red-400">
                          <span>Fears</span>
                          <span className="font-semibold">{npc.dna_profile?.fears?.join(', ') || "DEATH"}</span>
                        </div>
                      </div>

                      {/* Vital meters */}
                      <div className="flex flex-col gap-2 mt-1">
                        
                        {/* Health */}
                        <div>
                          <div className="flex justify-between text-[8px] font-semibold text-slate-400 mb-0.5">
                            <span>Health</span>
                            <span className={health < 50 ? 'text-red-400 font-bold' : 'text-slate-300'}>{health}%</span>
                          </div>
                          <div className="progress-bar-container">
                            <div 
                              className={`progress-bar-fill ${health < 50 ? 'bg-red-500' : 'bg-emerald-500'}`}
                              style={{ width: `${health}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Hunger & Sanity */}
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <div className="flex justify-between text-[8px] font-semibold text-slate-400 mb-0.5">
                              <span>Hunger</span>
                              <span className="text-slate-300">{hunger}%</span>
                            </div>
                            <div className="progress-bar-container">
                              <div className="progress-bar-fill bg-amber-500" style={{ width: `${hunger}%` }}></div>
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-[8px] font-semibold text-slate-400 mb-0.5">
                              <span>Sanity</span>
                              <span className="text-slate-300">{(sanity * 100).toFixed(0)}%</span>
                            </div>
                            <div className="progress-bar-container">
                              <div className="progress-bar-fill bg-cyan-400" style={{ width: `${sanity * 100}%` }}></div>
                            </div>
                          </div>
                        </div>

                      </div>

                    </div>
                  )
                })}
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/[0.06] bg-white/[0.015] flex">
              <button 
                onClick={() => setInspectEvent(null)}
                className="w-full py-2.5 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-bold rounded-lg text-xs transition duration-200 hover:brightness-110 shadow-lg shadow-pink-950/30"
              >
                Done Inspecting
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  )
}
