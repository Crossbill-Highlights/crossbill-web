import type { ChapterWithHighlights } from '@/api/generated/model';
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { NoteCard } from '@/pages/BookPage/Notes/NoteCard';
import { NoteModals } from '@/pages/BookPage/Notes/NoteModals';
import { useNoteModals } from '@/pages/BookPage/Notes/hooks/useNoteModals';
import { AddIcon } from '@/theme/Icons.tsx';
import { Box, Button, Stack, Typography } from '@mui/material';

interface NotesSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
}

export const NotesSection = ({ chapter, bookId }: NotesSectionProps) => {
  const { data, isLoading } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, {
    chapter_id: chapter.id,
  });
  const noteModals = useNoteModals();

  // NOTE: the orval axios mutator unwraps the response (`.then(({ data }) => data)`),
  // so the generated GET hook's `data` is the payload itself, not an AxiosResponse.
  const notes = data?.notes ?? [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={<AddIcon />}
          onClick={noteModals.openCreate}
        >
          Add note
        </Button>
      </Box>
      {isLoading && <Spinner />}
      {!isLoading && notes.length === 0 && (
        <Typography color="text.secondary">No notes linked to this chapter.</Typography>
      )}
      <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
        {notes.map((note) => (
          <li key={note.id}>
            <NoteCard note={note} onClick={() => noteModals.openView(note)} />
          </li>
        ))}
      </Stack>
      <NoteModals controller={noteModals} initialChapterIds={[chapter.id]} />
    </Box>
  );
};
