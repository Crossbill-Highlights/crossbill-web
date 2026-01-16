import { createFileRoute } from '@tanstack/react-router';
import { BookPage } from '@/pages/BookPage/BookPage';

type BookPageSearch = {
  search?: string;
  tagId?: number;
  highlightId?: number;
  tab?: 'highlights' | 'flashcards' | 'readingSessions';
  sessionPage?: number;
};
export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
  validateSearch: (search: Record<string, unknown>): BookPageSearch => {
    return {
      search: (search.search as string | undefined) || undefined,
      tagId: (search.tagId as number | undefined) || undefined,
      highlightId: (search.highlightId as number | undefined) || undefined,
      tab: (search.tab as 'highlights' | 'flashcards' | 'readingSessions' | undefined) || undefined,
      sessionPage: search.sessionPage ? Number(search.sessionPage) : undefined,
    };
  },
});
