import { StructurePage } from '@/pages/BookPage/Structure/StructurePage';
import { createFileRoute } from '@tanstack/react-router';

type StructureSearch = {
  chapterId?: number;
};

export const Route = createFileRoute('/book/$bookId/structure')({
  component: StructurePage,
  validateSearch: (search: Record<string, unknown>): StructureSearch => ({
    chapterId: (search.chapterId as number | undefined) || undefined,
  }),
});
