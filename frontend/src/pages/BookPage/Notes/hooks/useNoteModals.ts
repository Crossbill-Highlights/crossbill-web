import type { NoteWithLinks } from '@/api/generated/model';
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useDeleteNoteApiV1NotesNoteIdDelete,
} from '@/api/generated/notes/notes.ts';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

/**
 * Owns the open/edit/delete state for the note editor and delete-confirmation
 * dialogs, plus the delete mutation. Shared by every surface that lets a user
 * create/edit/delete notes (notes tab, chapter section, ...) so they don't each
 * re-declare the same state and handlers. Render the dialogs with `NoteModals`.
 */
export interface NoteModalsController {
  /** Open the editor to create a new note. */
  openCreate: () => void;
  /** Open the editor to edit an existing note. */
  openEdit: (note: NoteWithLinks) => void;
  /** Ask to delete a note (opens the confirmation dialog). */
  requestDelete: (note: NoteWithLinks) => void;

  // Consumed by NoteModals:
  editorOpen: boolean;
  editingNote: NoteWithLinks | null;
  closeEditor: () => void;
  deletingNote: NoteWithLinks | null;
  cancelDelete: () => void;
  confirmDelete: () => void;
  isDeleting: boolean;
}

export const useNoteModals = (bookId: number): NoteModalsController => {
  const queryClient = useQueryClient();
  const { showSnackbar } = useSnackbar();

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

  return {
    openCreate: () => {
      setEditingNote(null);
      setEditorOpen(true);
    },
    openEdit: (note) => {
      setEditingNote(note);
      setEditorOpen(true);
    },
    requestDelete: (note) => setDeletingNote(note),
    editorOpen,
    editingNote,
    closeEditor: () => setEditorOpen(false),
    deletingNote,
    cancelDelete: () => setDeletingNote(null),
    confirmDelete: () => {
      if (deletingNote) {
        void deleteMutation.mutateAsync({ noteId: deletingNote.id });
      }
    },
    isDeleting: deleteMutation.isPending,
  };
};
