import type { ChapterWithHighlights, NoteWithLinks } from '@/api/generated/model';
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useDeleteNoteApiV1NotesNoteIdDelete,
  useGetNotesForBookApiV1BooksBookIdNotesGet,
} from '@/api/generated/notes/notes.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { NoteCard } from '@/pages/BookPage/Notes/NoteCard';
import { NoteEditorDialog } from '@/pages/BookPage/Notes/NoteEditorDialog';
import { AddIcon } from '@/theme/Icons.tsx';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface NotesSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
}

export const NotesSection = ({ chapter, bookId }: NotesSectionProps) => {
  const { showSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const { data, isLoading } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, {
    chapter_id: chapter.id,
  });

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<NoteWithLinks | null>(null);
  const [deletingNote, setDeletingNote] = useState<NoteWithLinks | null>(null);

  const deleteMutation = useDeleteNoteApiV1NotesNoteIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(bookId),
        });
        setDeletingNote(null);
      },
      onError: (error) => {
        console.error('Failed to delete note:', error);
        showSnackbar('Failed to delete note. Please try again.', 'error');
      },
    },
  });

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
          onClick={() => {
            setEditingNote(null);
            setEditorOpen(true);
          }}
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
              onEdit={() => {
                setEditingNote(note);
                setEditorOpen(true);
              }}
              onDelete={() => setDeletingNote(note)}
            />
          </li>
        ))}
      </Stack>
      <NoteEditorDialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        note={editingNote}
        initialChapterIds={[chapter.id]}
      />
      <ConfirmationDialog
        open={deletingNote !== null}
        title="Delete note"
        message={`Delete note "${deletingNote?.title ?? ''}"? This cannot be undone.`}
        onConfirm={() => {
          if (deletingNote) {
            void deleteMutation.mutateAsync({ noteId: deletingNote.id });
          }
        }}
        onClose={() => setDeletingNote(null)}
        isLoading={deleteMutation.isPending}
      />
    </Box>
  );
};
