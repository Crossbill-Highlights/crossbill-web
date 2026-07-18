import type { ChapterWithHighlights } from '@/api/generated/model';
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { NoteCard } from '@/pages/BookPage/Notes/NoteCard';
import { NoteModals } from '@/pages/BookPage/Notes/NoteModals';
import { NotePickerDialog } from '@/pages/BookPage/Notes/components/NotePickerDialog.tsx';
import { useNoteLinks } from '@/pages/BookPage/Notes/hooks/useNoteLinks';
import { useNoteModals } from '@/pages/BookPage/Notes/hooks/useNoteModals';
import { AddIcon, LinkIcon, LinkOffIcon } from '@/theme/Icons.tsx';
import { Box, Button, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { useState } from 'react';

interface NotesSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
}

export const NotesSection = ({ chapter, bookId }: NotesSectionProps) => {
  const { data, isLoading } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, {
    chapter_id: chapter.id,
  });
  const noteModals = useNoteModals({ syncToUrl: false });
  const [pickerOpen, setPickerOpen] = useState(false);
  const noteLinks = useNoteLinks({ bookId });

  // NOTE: the orval axios mutator unwraps the response (`.then(({ data }) => data)`),
  // so the generated GET hook's `data` is the payload itself, not an AxiosResponse.
  const notes = data?.notes ?? [];

  const isDisabled = noteLinks.isPending;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={<LinkIcon />}
          onClick={() => setPickerOpen(true)}
          disabled={isDisabled}
        >
          Link existing note
        </Button>
        <Button
          variant="outlined"
          size="small"
          startIcon={<AddIcon />}
          onClick={noteModals.openCreate}
          disabled={isDisabled}
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
            <NoteCard
              note={note}
              onClick={() => noteModals.openView(note)}
              action={
                <Tooltip title="Unlink from chapter">
                  <IconButton
                    aria-label="Unlink note"
                    size="small"
                    disabled={isDisabled}
                    onClick={(event) => {
                      event.stopPropagation();
                      noteLinks.unlinkChapter(note, chapter.id);
                    }}
                  >
                    <LinkOffIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              }
            />
          </li>
        ))}
      </Stack>
      <NoteModals controller={noteModals} initialChapterIds={[chapter.id]} />
      <NotePickerDialog
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        bookId={bookId}
        title="Add chapter to note"
        onSelect={(note) =>
          noteLinks.linkChapter(note, chapter.id, { onSuccess: () => setPickerOpen(false) })
        }
      />
    </Box>
  );
};
