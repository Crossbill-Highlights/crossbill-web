import { StructureTab } from '@/pages/BookPage/StructureTab/StructureTab';
import { createFileRoute } from '@tanstack/react-router';

type StructureSearch = {
  chapterId?: number;
};

export const Route = createFileRoute('/book/$bookId/structure')({
  component: StructureTab,
  validateSearch: (search: Record<string, unknown>): StructureSearch => ({
    chapterId: (search.chapterId as number | undefined) || undefined,
  }),
});
