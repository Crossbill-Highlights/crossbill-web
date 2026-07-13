import type {
  GetNotesForBookApiV1BooksBookIdNotesGetParams,
  NoteWithLinks,
} from '@/api/generated/model';
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useDeleteNoteApiV1NotesNoteIdDelete,
  useGetNotesForBookApiV1BooksBookIdNotesGet,
} from '@/api/generated/notes/notes.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { AddIcon } from '@/theme/Icons.tsx';
import { Box, Button, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useState } from 'react';

import { NoteCard } from './NoteCard';
import { NoteEditorDialog } from './NoteEditorDialog';
import { NOTE_KIND_LABELS, NOTE_KINDS, type NoteKindValue } from './noteKinds';

interface NoteKindFilterProps {
  value: NoteKindValue | null;
  onChange: (value: NoteKindValue | null) => void;
}

const NoteKindFilter = ({ value, onChange }: NoteKindFilterProps) => (
  <ToggleButtonGroup
    size="small"
    exclusive
    value={value}
    onChange={(_, next: NoteKindValue | null) => onChange(next)}
  >
    {NOTE_KINDS.map((kind) => (
      <ToggleButton key={kind} value={kind}>
        {NOTE_KIND_LABELS[kind]}
      </ToggleButton>
    ))}
  </ToggleButtonGroup>
);

export const NotesPage = () => {
  const { book } = useBookPage();
  const { showSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const navigate = useNavigate({ from: '/book/$bookId/notes' });
  const { kind, chapterId, tagId } = useSearch({ from: '/book/$bookId/notes' });

  const params: GetNotesForBookApiV1BooksBookIdNotesGetParams = {
    kind: (kind as NoteKindValue | undefined) ?? undefined,
    chapter_id: chapterId,
    highlight_tag_id: tagId,
  };
  const { data, isLoading, isError } = useGetNotesForBookApiV1BooksBookIdNotesGet(book.id, params);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<NoteWithLinks | null>(null);
  const [deletingNote, setDeletingNote] = useState<NoteWithLinks | null>(null);

  const deleteMutation = useDeleteNoteApiV1NotesNoteIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(book.id),
        });
        setDeletingNote(null);
      },
      onError: (error) => {
        console.error('Failed to delete note:', error);
        showSnackbar('Failed to delete note. Please try again.', 'error');
      },
    },
  });

  const handleKindFilter = (value: NoteKindValue | null) => {
    void navigate({ search: (prev) => ({ ...prev, kind: value ?? undefined }) });
  };

  // NOTE: the orval axios mutator unwraps the response (`.then(({ data }) => data)`),
  // so the generated GET hook's `data` is the payload itself, not an AxiosResponse.
  const notes = data?.notes ?? [];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <NoteKindFilter
          value={(kind as NoteKindValue | undefined) ?? null}
          onChange={handleKindFilter}
        />
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingNote(null);
            setEditorOpen(true);
          }}
        >
          New note
        </Button>
      </Box>

      {isLoading && <Spinner />}
      {isError && <Typography color="error">Failed to load notes.</Typography>}
      {!isLoading && !isError && notes.length === 0 && (
        <Typography color="text.secondary">
          No notes yet. Create notes about characters, terms, and concepts as you read.
        </Typography>
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

      <NoteEditorDialog open={editorOpen} onClose={() => setEditorOpen(false)} note={editingNote} />
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
