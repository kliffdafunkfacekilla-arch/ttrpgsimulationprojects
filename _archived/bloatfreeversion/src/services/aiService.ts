/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { AISettings, Document, Blueprint } from "../types";

export interface LorekeeperReport {
  missingDetails: string[];
  inventedLore: string[];
  isClean: boolean;
  critique?: string; 
}

export class AIService {
  private settings: AISettings;

  constructor(settings: AISettings) {
    this.settings = settings;
  }

  private repairJson(jsonString: string): string {
    let repaired = jsonString.trim().replace(/,\s*$/, "");
    const stack: string[] = [];
    for (const char of repaired) {
      if (char === '{') stack.push('}');
      if (char === '[') stack.push(']');
      if (char === '}' || char === ']') stack.pop();
    }
    return repaired + stack.reverse().join("");
  }

  async planStructure(docs: Document[]): Promise<Blueprint> {
    const context = docs.map(d => `Title: ${d.title}\nContent: ${d.content.substring(0, 100)}`).join('\n\n');
    const prompt = `Organize these documents into chapters. JSON ONLY: { "chapters": [{ "title": "string", "description": "string", "documents": ["Doc Title"] }] }\nDATA: ${context}`;
    const raw = await this.callOllama(prompt, true);
    try { return JSON.parse(raw); } catch { return JSON.parse(this.repairJson(raw)); }
  }

  async rewriteChapter(title: string, content: string, tone: string, note?: string): Promise<string> {
    const prompt = `Write TTRPG lore for "${title}". Tone: ${tone}. ${note ? `FIX: ${note}` : ""} RAW DATA: ${content}`;
    return await this.callOllama(prompt, false);
  }

  async reviewChapter(raw: string, gen: string): Promise<LorekeeperReport> {
    const prompt = `Compare RAW vs GEN. JSON ONLY: { "isClean": boolean, "critique": "summary" }\nRAW: ${raw}\nGEN: ${gen}`;
    const rawRep = await this.callOllama(prompt, true);
    try { return JSON.parse(rawRep); } catch { return JSON.parse(this.repairJson(rawRep)); }
  }

  async generateImage(prompt: string): Promise<string> {
    const response = await fetch(`http://127.0.0.1:7860/sdapi/v1/txt2img`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        prompt: `${prompt}, fantasy digital art, high quality`,
        steps: 20, width: 512, height: 512 
      })
    });
    const data = await response.json();
    return `data:image/png;base64,${data.images[0]}`;
  }

  private async callOllama(prompt: string, json: boolean): Promise<string> {
    const res = await fetch(`${this.settings.ollamaEndpoint}/api/generate`, {
      method: 'POST',
      body: JSON.stringify({ 
        model: this.settings.ollamaModel, 
        prompt, 
        stream: false, 
        format: json ? 'json' : undefined,
        options: { num_predict: 4096, temperature: 0.2 } 
      })
    });
    const data = await res.json();
    return data.response;
  }
}