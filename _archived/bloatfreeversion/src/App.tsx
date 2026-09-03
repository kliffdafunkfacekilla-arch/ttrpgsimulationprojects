/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { Document, Blueprint, ProcessedChapter, AISettings, BookTheme } from './types';
import { AIService, LorekeeperReport } from './services/aiService';
import { Settings, BookOpen, FolderPlus, Play, CheckCircle, Loader2, RefreshCw, Palette, Image as ImageIcon, Sparkles } from 'lucide-react';

const THEMES: BookTheme[] = [
  { id: 'classic', name: 'Classic Parchment', bgOuter: '#f4ece1', bgInner: '#fffefc', textColor: '#2e2e2e', headingColor: '#8b0000', accentColor: '#d3c5b0', fontFamily: "'Crimson Text', serif" },
  { id: 'dark-necromancy', name: 'Dark Necromancy', bgOuter: '#111111', bgInner: '#1a1a1a', textColor: '#d4d4d4', headingColor: '#4ade80', accentColor: '#333333', fontFamily: "'Space Grotesk', sans-serif" }
];

export default function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeTab, setActiveTab] = useState<'editor' | 'agents' | 'preview'>('editor');
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null);
  const [processedChapters, setProcessedChapters] = useState<ProcessedChapter[]>([]);
  const [generatedImages, setGeneratedImages] = useState<Record<string, string>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeThemeId, setActiveThemeId] = useState('classic');
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const [settings] = useState<AISettings>({
    provider: 'ollama', ollamaEndpoint: 'http://localhost:11434', ollamaModel: 'llama3', toneId: 'survivor'
  });

  const handleImport = async (e: any) => {
    const files = Array.from(e.target.files || []) as File[];
    const docs = await Promise.all(files.map(async f => ({ id: crypto.randomUUID(), title: f.name.replace(/\.[^/.]+$/, ""), content: await f.text() })));
    setDocuments(prev => [...prev, ...docs]);
  };

  // --- AUTOMATIC ONE-BY-ONE IMAGE QUEUE ---
  const runAutoImageGeneration = async () => {
    const ai = new AIService(settings);
    for (const chapter of processedChapters) {
      const markers = chapter.htmlContent.match(/\[\[IMAGE_HERE:.*?\]\]/g) || [];
      for (let i = 0; i < markers.length; i++) {
        const prompt = markers[i].replace('[[IMAGE_HERE: ', '').replace(']]', '');
        const imageId = `img-${chapter.title}-${i}`;
        if (!generatedImages[imageId]) {
          setGeneratingId(imageId);
          try {
            const base64 = await ai.generateImage(prompt);
            setGeneratedImages(prev => ({ ...prev, [imageId]: base64 }));
          } catch (e) { console.error("Image failed:", imageId); }
        }
      }
    }
    setGeneratingId(null);
  };

  const renderContent = (chapterTitle: string, html: string) => {
    const parts = html.split(/(\[\[IMAGE_HERE:.*?\]\])/g);
    let imgIdx = 0;
    return parts.map((part, i) => {
      if (part.startsWith('[[IMAGE_HERE:')) {
        const id = `img-${chapterTitle}-${imgIdx++}`;
        return (
          <div key={i} className="my-8 border-2 border-dashed border-zinc-200 p-4 rounded text-center">
            {generatedImages[id] ? (
              <img src={generatedImages[id]} className="mx-auto rounded shadow-lg" />
            ) : (
              <div className="flex flex-col items-center gap-2 py-4">
                <ImageIcon className="w-6 h-6 text-zinc-300" />
                {generatingId === id && <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />}
              </div>
            )}
          </div>
        );
      }
      return <div key={i} dangerouslySetInnerHTML={{ __html: part }} />;
    });
  };

  const activeTheme = THEMES.find(t => t.id === activeThemeId)!;

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 font-sans">
      <div className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col p-4">
        <h1 className="font-bold flex items-center gap-2 mb-6"><BookOpen className="w-4 h-4 text-emerald-500" /> Lore Formatter</h1>
        <label className="w-full flex items-center justify-center gap-2 bg-zinc-800 py-2 rounded-md text-xs cursor-pointer mb-4">
          <FolderPlus className="w-4 h-4" /> Import Folder
          <input type="file" {...{ webkitdirectory: "", directory: "" }} multiple onChange={handleImport} className="hidden" />
        </label>
        <div className="flex-1 overflow-y-auto">
          {documents.map(d => <div key={d.id} className="p-2 text-[10px] text-zinc-500 bg-zinc-950/50 mb-1 rounded">{d.title}</div>)}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="h-14 border-b border-zinc-800 flex items-center justify-between px-4">
          <div className="flex gap-6">
            <button onClick={() => setActiveTab('editor')}>Editor</button>
            <button onClick={() => setActiveTab('agents')}>Orchestrator</button>
            <button onClick={() => setActiveTab('preview')}>Preview</button>
          </div>
          {activeTab === 'preview' && processedChapters.length > 0 && (
            <button onClick={runAutoImageGeneration} className="bg-emerald-600 px-4 py-1.5 rounded text-xs font-bold flex items-center gap-2">
              <Sparkles className="w-3 h-3" /> Auto-Generate All Visuals
            </button>
          )}
        </div>

        <div className="flex-1 overflow-auto p-12" style={{ backgroundColor: activeTheme.bgInner, color: activeTheme.textColor, fontFamily: activeTheme.fontFamily }}>
          {activeTab === 'preview' && processedChapters.map((ch, i) => (
            <div key={i} className="mb-20 max-w-4xl mx-auto">
              <h1 className="text-4xl border-b-2 mb-6" style={{ color: activeTheme.headingColor, borderColor: activeTheme.accentColor }}>{ch.title}</h1>
              <div className="leading-relaxed space-y-4">{renderContent(ch.title, ch.htmlContent)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}