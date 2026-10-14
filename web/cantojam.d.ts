// Types for web/cantojam.js, the JavaScript port of the Python package.
// Covers the functions other projects import. The parity test keeps the
// behaviour identical to Python; keep these signatures in step by hand.

export interface Syllable {
  char: string;
  jyutping: string | null;
  tone: string | null;
  source: "corpus" | "curated" | "override" | null;
  ambiguous: boolean;
  skipped: boolean;
  latin: boolean;
}

export interface CheckRow {
  index: number;
  char: string;
  jyutping: string | null;
  tone: string | null;
  midi: number | null;
  note: string | null;
  violation: boolean;
  unusual: boolean;
  message?: string;
}

export interface CheckResult {
  rows: CheckRow[];
  violations: CheckRow[];
  unusual: CheckRow[];
  syllables: number;
  notes: number;
  length_mismatch: boolean;
}

export interface RepairOption {
  /** Index of the first sung syllable replaced. */
  start: number;
  length: number;
  replaces: string;
  word: string;
  jyutping: string;
  tones: string;
  rime: string;
  /** Times the corpus used this word. */
  count: number;
  /** Polyphones sung with a non-default reading, e.g. "爲=wai4". */
  pin: string[];
  /** The whole line with the replacement made (sung syllables only). */
  line: string;
}

export interface RepairProblem {
  index: number;
  kind: "violation" | "unusual";
  message: string;
  phrases: RepairOption[];
  singles: RepairOption[];
  phraseTotal: number;
  singleTotal: number;
}

export interface RepairReport {
  check: CheckResult;
  problems: RepairProblem[];
  clean: boolean;
  line: string;
}

export interface RepairOptions {
  keepRhyme?: boolean;
  minCount?: number;
  limit?: number;
  allowUnusual?: boolean;
  overrides?: Record<string, string>;
}

export const NOTE_NAMES: string[];
export const SCALES: Record<string, number[]>;
export const TONE_NAMES: Record<string, string>;
export const corpusSongs: number;
export const corpusSyllables: number;

export function syllabify(text: string, overrides?: Record<string, string>): Syllable[];
export function readings(char: string, overrides?: Record<string, string>): string[];
export function toneOf(jyutping: string | null): string | null;
export function check(text: string, melody: number[] | string, overrides?: Record<string, string>): CheckResult;
export function noteName(midi: number): string;
export function parseNote(token: string | number): number;

/** Load the corpus word list (about 700 KB). Required before repairs(). */
export function loadWords(): Promise<unknown[]>;
export function wordsLoaded(): boolean;
/** For each clash, corpus words that sit on those notes. Call loadWords() first. */
export function repairs(text: string, melody: number[] | string, options?: RepairOptions): RepairReport;
