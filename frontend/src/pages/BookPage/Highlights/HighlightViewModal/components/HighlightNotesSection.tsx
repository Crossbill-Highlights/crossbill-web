import type { Highlight, NoteUpdateRequest, NoteWithLinks } from '@/api/generated/model';
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useUpdateNoteApiV1NotesNoteIdPut,
} from '@/api/generated/notes/notes.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { NoteCard } from '@/pages/BookPage/Notes/NoteCard';
import { NoteModals } from '@/pages/BookPage/Notes/NoteModals';
import { useNoteModals } from '@/pages/BookPage/Notes/hooks/useNoteModals';
import { AddIcon, LinkIcon } from '@/theme/Icons.tsx';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { NotePickerDialog } from './NotePickerDialog.tsx';

interface HighlightNotesSectionProps {
  highlight: Highlight;
  bookId: number;
  /** Notes linked to the highlight; the query lives in HighlightTabs for the tab count. */
  notes: NoteWithLinks[];
  isLoading: boolean;
  disabled?: boolean;
}

/**
 * Notes tab of the highlight modal: lists notes linked to the highlight and
 * offers creating a new pre-linked note or linking an existing one. Creating
 * and linking both invalidate the notes-for-book query (prefix match), so the
 * filtered list here refreshes immediately.
 */
export const HighlightNotesSection = ({
  highlight,
  bookId,
  notes,
  isLoading,
  disabled = false,
}: HighlightNotesSectionProps) => {
  const queryClient = useQueryClient();
  const { showSnackbar } = useSnackbar();
  const noteModals = useNoteModals({ syncToUrl: false });
  const [pickerOpen, setPickerOpen] = useState(false);

  const updateNoteMutation = useUpdateNoteApiV1NotesNoteIdPut({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(bookId),
        });
        setPickerOpen(false);
        showSnackbar('Highlight added to note.', 'success');
      },
      onError: (error: Error) => {
        console.error('Failed to add highlight to note:', error);
        showSnackbar('Failed to add highlight to note. Please try again.', 'error');
      },
    },
  });

  const handleAddToExistingNote = async (note: NoteWithLinks) => {
    const payload: NoteUpdateRequest = {
      title: note.title,
      body: note.body,
      kind: note.kind as NoteUpdateRequest['kind'],
      chapter_ids: note.chapter_ids,
      highlight_ids: [...new Set([...note.highlight_ids, highlight.id])],
      tag_ids: note.tag_ids,
    };
    await updateNoteMutation.mutateAsync({ noteId: note.id, data: payload });
  };

  const isDisabled = disabled || updateNoteMutation.isPending;

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
        <Typography color="text.secondary">No notes linked to this highlight.</Typography>
      )}
      <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
        {notes.map((note) => (
          <li key={note.id}>
            <NoteCard note={note} onClick={() => noteModals.openView(note)} />
          </li>
        ))}
      </Stack>
      <NoteModals
        controller={noteModals}
        initialChapterIds={highlight.chapter_id ? [highlight.chapter_id] : []}
        initialHighlightIds={[highlight.id]}
      />
      <NotePickerDialog
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        bookId={bookId}
        onSelect={(note) => void handleAddToExistingNote(note)}
      />
    </Box>
  );
};
