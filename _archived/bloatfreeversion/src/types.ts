export interface Document {
  id: string;
  title: string;
  content: string;
}

export interface Blueprint {
  chapters: {
    title: string;
    description: string;
    documents: string[]; // Document IDs
  }[];
}

export interface ProcessedChapter {
  title: string;
  htmlContent: string;
}

export interface LorekeeperReport {
  chapterTitle: string;
  missingDetails: string[];
  inventedLore: string[];
  inconsistencies: string[];
  isClean: boolean;
}

export interface BookTheme {
  id: string;
  name: string;
  bgOuter: string;
  bgInner: string;
  textColor: string;
  headingColor: string;
  accentColor: string;
  fontFamily: string;
}

export interface TonePreset {
  id: string;
  name: string;
  prompt: string;
}

export interface AISettings {
  provider: 'gemini' | 'ollama';
  geminiModel: string;
  ollamaEndpoint: string;
  ollamaModel: string;
  toneId: string;
}

