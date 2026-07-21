import type { BookReflectionResponse } from '@/api/generated/model';

export type ReflectionField = 'what_is_it_about' | 'what_does_it_say' | 'do_i_agree' | 'so_what';

export interface ReflectionQuestion {
  field: ReflectionField;
  title: string;
  guide: string;
}

export const REFLECTION_QUESTIONS: ReflectionQuestion[] = [
  {
    field: 'what_is_it_about',
    title: 'What is the book about?',
    guide:
      'State what the whole book is about in a single sentence. Then outline its major parts, and name the problems the author set out to solve.',
  },
  {
    field: 'what_does_it_say',
    title: 'What does it say in detail?',
    guide:
      "The author's key terms, most important propositions, and the arguments behind them. Link your term and concept notes below — that's how you come to terms with the author.",
  },
  {
    field: 'do_i_agree',
    title: 'Do I agree?',
    guide:
      'Judge the book. Is the author uninformed (missing something important), misinformed (working from false premises), or illogical (reasoning doesn’t hold)? If none apply, you are obligated to agree — say so.',
  },
  {
    field: 'so_what',
    title: 'So what?',
    guide:
      "If the book is true, what follows? What will you do or think differently? How does it connect with other books you've read?",
  },
];

export const emptyReflection = (bookId: number): BookReflectionResponse => ({
  book_id: bookId,
  what_is_it_about: '',
  what_does_it_say: '',
  do_i_agree: '',
  so_what: '',
  note_ids: [],
});
