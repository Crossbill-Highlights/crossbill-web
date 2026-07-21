export const READING_STAGES = ['to_read', 'skimming', 'reading', 'finished', 'reflected'] as const;

export type ReadingStageValue = (typeof READING_STAGES)[number];

export const READING_STAGE_LABELS: Record<ReadingStageValue, string> = {
  to_read: 'To read',
  skimming: 'Skimming',
  reading: 'Reading',
  finished: 'Finished',
  reflected: 'Reflected',
};

export const READING_STAGE_HINTS: Partial<Record<ReadingStageValue, string>> = {
  skimming: 'After skimming, try stating what the book is about.',
  finished: "You've finished the book — a good time for 'Do I agree?'",
  reflected: "You've reflected on this book — revisit your answers whenever it comes up again.",
};
