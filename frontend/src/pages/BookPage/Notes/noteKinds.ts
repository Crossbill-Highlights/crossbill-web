export const NOTE_KINDS = ['character', 'term', 'concept', 'other'] as const;

export type NoteKindValue = (typeof NOTE_KINDS)[number];

export const NOTE_KIND_LABELS: Record<NoteKindValue, string> = {
  character: 'Character',
  term: 'Term',
  concept: 'Concept',
  other: 'Other',
};
