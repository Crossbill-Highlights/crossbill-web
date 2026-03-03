import { StructureTab } from '@/pages/BookPage/StructureTab/StructureTab';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId/structure')({
  component: StructureTab,
});
