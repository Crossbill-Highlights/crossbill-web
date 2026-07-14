import { NotesPage } from '@/pages/BookPage/Notes/NotesPage';
import { createFileRoute } from '@tanstack/react-router';

type NotesSearch = {
  kind?: string;
  chapterId?: number;
  tagId?: number;
  noteId?: number;
};

export const Route = createFileRoute('/book/$bookId/notes')({
  component: NotesPage,
  validateSearch: (search: Record<string, unknown>): NotesSearch => ({
    kind: (search.kind as string | undefined) || undefined,
    chapterId: (search.chapterId as number | undefined) || undefined,
    tagId: (search.tagId as number | undefined) || undefined,
    noteId: (search.noteId as number | undefined) || undefined,
  }),
});
