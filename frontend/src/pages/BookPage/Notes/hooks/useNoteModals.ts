import type { NoteWithLinks } from '@/api/generated/model';
import { useState } from 'react';

/**
 * Owns the open state for the note editor (create) and the note detail modal.
 * Shared by every surface that lists notes (notes tab, chapter section, ...) so
 * they don't each re-declare the same state. Render the dialogs with `NoteModals`.
 *
 * Editing and deleting an existing note happen inside `NoteViewModal` itself
 * (read-only view that toggles to editable), so the controller only tracks which
 * note is open and whether the create editor is open.
 */
export interface NoteModalsController {
  /** Open the editor to create a new note. */
  openCreate: () => void;
  /** Open the detail modal for an existing note. */
  openView: (note: NoteWithLinks) => void;

  // Consumed by NoteModals:
  editorOpen: boolean;
  closeEditor: () => void;
  viewingNote: NoteWithLinks | null;
  closeView: () => void;
}

export const useNoteModals = (): NoteModalsController => {
  const [editorOpen, setEditorOpen] = useState(false);
  const [viewingNote, setViewingNote] = useState<NoteWithLinks | null>(null);

  return {
    openCreate: () => setEditorOpen(true),
    openView: (note) => setViewingNote(note),
    editorOpen,
    closeEditor: () => setEditorOpen(false),
    viewingNote,
    closeView: () => setViewingNote(null),
  };
};
