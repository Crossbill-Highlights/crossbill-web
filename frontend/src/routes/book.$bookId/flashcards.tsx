import { FlashcardsPage } from '@/pages/BookPage/Flashcards/FlashcardsPage';
import { createFileRoute } from '@tanstack/react-router';

type FlashcardsSearch = {
  search?: string;
  tagId?: number;
  chapterId?: number;
};

export const Route = createFileRoute('/book/$bookId/flashcards')({
  component: FlashcardsPage,
  validateSearch: (search: Record<string, unknown>): FlashcardsSearch => ({
    search: (search.search as string | undefined) || undefined,
    tagId: (search.tagId as number | undefined) || undefined,
    chapterId: (search.chapterId as number | undefined) || undefined,
  }),
});
