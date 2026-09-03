import React, { useState, useEffect } from 'react'
import { X, Save, Sliders, Eye, RefreshCw, AlertCircle, Sparkles, Settings } from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://localhost:8000/api"

export default function SettingsPanel({ onClose }) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  // Core simulation multipliers
  const [metabolismRate, setMetabolismRate] = useState(1.0)
  const [magicFlow, setMagicFlow] = useState(1.0)
  const [cropYield, setCropYield] = useState(1.0)

  // Logger configs
  const [logLevel, setLogLevel] = useState("HIGH")
  const [watchedEvents, setWatchedEvents] = useState(["FAMINE", "SIEGE", "STORM", "REBELLION"])

  // Preserved database overrides
  const [speciesModifiers, setSpeciesModifiers] = useState({})
  const [factionModifiers, setFactionModifiers] = useState({})

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`${API_BASE}/settings`)
      const data = res.data
      setMetabolismRate(data.global_metabolism_rate ?? 1.0)
      setMagicFlow(data.global_magic_flow ?? 1.0)
      setCropYield(data.base_crop_yield ?? 1.0)
      
      const specMods = data.species_modifiers || {}
      setSpeciesModifiers(specMods)
      setFactionModifiers(data.faction_modifiers || {})

      // Parse custom logger configs stored under species_modifiers._logger
      if (specMods._logger) {
        setLogLevel(specMods._logger.log_level || "HIGH")
        setWatchedEvents(specMods._logger.watched_events || ["FAMINE", "SIEGE", "STORM", "REBELLION"])
      }
    } catch (err) {
      console.error("Failed to load settings:", err)
      setError("Failed to fetch world settings from active PostgreSQL instance.")
    } finally {
      setLoading(false)
    }
  }

  const handleToggleEvent = (event) => {
    if (watchedEvents.includes(event)) {
      setWatchedEvents(watchedEvents.filter(e => e !== event))
    } else {
      setWatchedEvents([...watchedEvents, event])
    }
  }

  const saveSettings = async () => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      // Pack the logger config in species_modifiers._logger persistently
      const updatedSpeciesMods = {
        ...speciesModifiers,
        _logger: {
          log_level: logLevel,
          watched_events: watchedEvents
        }
      }

      const payload = {
        global_metabolism_rate: parseFloat(metabolismRate),
        global_magic_flow: parseFloat(magicFlow),
        base_crop_yield: parseFloat(cropYield),
        species_modifiers: updatedSpeciesMods,
        faction_modifiers: factionModifiers
      }

      await axios.post(`${API_BASE}/settings`, payload)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      console.error("Failed to save settings:", err)
      setError("Failed to save configuration settings to database.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-[9999] flex items-center justify-center p-4">
      <div className="bg-[#0b0e16]/95 border border-white/[0.08] rounded-2xl max-w-xl w-full shadow-2xl relative flex flex-col max-h-[90vh] overflow-hidden animate-slide-up">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-full bg-white/[0.02] hover:bg-white/[0.08] text-slate-400 hover:text-white transition border border-white/[0.05]"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Panel Header */}
        <div className="p-6 border-b border-white/[0.06] bg-white/[0.01] flex items-center gap-3">
          <div className="p-2 bg-purple-500/10 border border-purple-500/20 rounded-lg">
            <Settings className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-md font-bold text-slate-100 uppercase tracking-wider font-mono">World Engine Settings</h2>
            <p className="text-[11px] text-slate-400 mt-0.5 uppercase tracking-widest font-medium">Shaping Ostraka's Chemistry & Physics</p>
          </div>
        </div>

        {/* Panel Content */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-400 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
              <span>Querying Ostraka settings...</span>
            </div>
          ) : (
            <>
              {error && (
                <div className="p-3 bg-red-950/30 border border-red-800/40 rounded-xl text-red-400 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {success && (
                <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-emerald-400 text-xs flex items-center gap-2 animate-bounce">
                  <Sparkles className="w-4 h-4 shrink-0" />
                  <span>Settings committed to PostgreSQL! Reality shifted.</span>
                </div>
              )}

              {/* 1. Core Physics Multipliers */}
              <div>
                <h3 className="section-title flex items-center gap-2 mb-4 font-mono"><Sliders className="w-4 h-4" /> Physics Multipliers</h3>
                <div className="flex flex-col gap-5">
                  
                  {/* Metabolism Rate */}
                  <div className="bg-white/[0.015] border border-white/[0.04] p-4 rounded-xl flex flex-col gap-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-300">Global Metabolism Rate</span>
                      <span className="font-mono text-purple-400 font-bold bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">{metabolismRate.toFixed(1)}x</span>
                    </div>
                    <input 
                      type="range"
                      min="0.1"
                      max="5.0"
                      step="0.1"
                      value={metabolismRate}
                      onChange={(e) => setMetabolismRate(parseFloat(e.target.value))}
                      className="w-full accent-purple-500 cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-500">Scales hourly demographic and individual entity food consumption levels.</span>
                  </div>

                  {/* Magic Volatility */}
                  <div className="bg-white/[0.015] border border-white/[0.04] p-4 rounded-xl flex flex-col gap-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-300">Magic Flow & Volatility</span>
                      <span className="font-mono text-pink-400 font-bold bg-pink-500/10 px-2 py-0.5 rounded border border-pink-500/20">{magicFlow.toFixed(1)}x</span>
                    </div>
                    <input 
                      type="range"
                      min="0.1"
                      max="5.0"
                      step="0.1"
                      value={magicFlow}
                      onChange={(e) => setMagicFlow(parseFloat(e.target.value))}
                      className="w-full accent-pink-500 cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-500">Amplifies chaotic supernatural storm mutation rates and aetheric volatility checks.</span>
                  </div>

                  {/* Crop Yield */}
                  <div className="bg-white/[0.015] border border-white/[0.04] p-4 rounded-xl flex flex-col gap-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-300">Base Crop Yield Multiplier</span>
                      <span className="font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">{cropYield.toFixed(1)}x</span>
                    </div>
                    <input 
                      type="range"
                      min="0.1"
                      max="5.0"
                      step="0.1"
                      value={cropYield}
                      onChange={(e) => setCropYield(parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-500">Modulates regional grain production yield during Day Shift hours.</span>
                  </div>

                </div>
              </div>

              {/* 2. Simulation Logger Configuration */}
              <div className="border-t border-white/[0.06] pt-6">
                <h3 className="section-title flex items-center gap-2 mb-4 font-mono"><Eye className="w-4 h-4" /> Logger Settings</h3>
                <div className="bg-white/[0.015] border border-white/[0.04] p-4 rounded-xl flex flex-col gap-4">
                  
                  {/* Log Level Select */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-slate-300">Telemetry Detail Level</label>
                    <select 
                      value={logLevel} 
                      onChange={(e) => setLogLevel(e.target.value)}
                      className="w-full bg-[#0e111a] border border-white/[0.08] rounded-lg p-2 text-xs font-medium text-slate-300 outline-none focus:border-purple-500 transition"
                    >
                      <option value="LOW">LOW - Basic economic & incident summaries</option>
                      <option value="MEDIUM">MEDIUM - Standard reports & warfare casualties</option>
                      <option value="HIGH">HIGH - Deep snapshots of surviving NPCs (TTRPG Hooks)</option>
                    </select>
                  </div>

                  {/* Watched Events Checkboxes */}
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-semibold text-slate-300">Watched Narrative Events</label>
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      {["FAMINE", "SIEGE", "STORM", "REBELLION"].map((event) => {
                        const isChecked = watchedEvents.includes(event)
                        return (
                          <label 
                            key={event} 
                            className={`flex items-center gap-2 bg-[#0e111a] border rounded-lg p-2.5 cursor-pointer text-xs font-semibold select-none transition ${
                              isChecked ? 'border-purple-500/50 bg-purple-500/[0.02] text-purple-300' : 'border-white/[0.05] text-slate-400 hover:border-white/[0.1]'
                            }`}
                          >
                            <input 
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => handleToggleEvent(event)}
                              className="accent-purple-500 cursor-pointer rounded"
                            />
                            <span>{event}</span>
                          </label>
                        )
                      })}
                    </div>
                  </div>

                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-white/[0.06] bg-white/[0.015] flex gap-3">
          <button 
            onClick={onClose}
            className="flex-1 py-2.5 px-4 bg-white/[0.02] hover:bg-white/[0.08] text-slate-300 font-semibold rounded-lg text-xs border border-white/[0.06] transition"
          >
            Cancel
          </button>
          <button 
            onClick={saveSettings}
            disabled={saving || loading}
            className="flex-1 simulate-btn py-2.5 flex items-center justify-center gap-1.5"
          >
            {saving ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            <span>{saving ? "SAVING..." : "COMMIT REALITY"}</span>
          </button>
        </div>

      </div>
    </div>
  )
}
