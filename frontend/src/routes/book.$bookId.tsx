import { BookPage } from '@/pages/BookPage/BookPage';
import { createFileRoute } from '@tanstack/react-router';

type BookPageSearch = {
  search?: string;
  tagId?: number;
  labelId?: number;
  highlightId?: number;
  chapterId?: number;
  tab?: 'highlights' | 'flashcards' | 'readingSessions' | 'structure';
  sessionPage?: number;
};
export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
  validateSearch: (search: Record<string, unknown>): BookPageSearch => {
    return {
      search: (search.search as string | undefined) || undefined,
      tagId: (search.tagId as number | undefined) || undefined,
      labelId: (search.labelId as number | undefined) || undefined,
      highlightId: (search.highlightId as number | undefined) || undefined,
      chapterId: (search.chapterId as number | undefined) || undefined,
      tab:
        (search.tab as 'highlights' | 'flashcards' | 'readingSessions' | 'structure' | undefined) ||
        undefined,
      sessionPage: search.sessionPage ? Number(search.sessionPage) : undefined,
    };
  },
});
