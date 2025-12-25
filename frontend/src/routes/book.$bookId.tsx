import { createFileRoute } from '@tanstack/react-router';
import { BookPage } from '../components/BookPage/BookPage';

type BookPageSearch = {
  search?: string;
  tagId?: number;
  highlightId?: number;
  tab?: 'highlights' | 'flashcards';
};
export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
  validateSearch: (search: Record<string, unknown>): BookPageSearch => {
    return {
      search: (search?.search as string) || undefined,
      tagId: (search?.tagId as number) || undefined,
      highlightId: (search?.highlightId as number) || undefined,
      tab: (search?.tab as 'highlights' | 'flashcards') || undefined,
    };
  },
});
