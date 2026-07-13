import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';

import { NoteEditorDialog } from './NoteEditorDialog';
import type { NoteModalsController } from './hooks/useNoteModals';

interface NoteModalsProps {
  controller: NoteModalsController;
  /** Pre-link created notes to these chapters (e.g. from the chapter section). */
  initialChapterIds?: number[];
}

/**
 * Renders the note editor and delete-confirmation dialogs for a
 * `useNoteModals` controller, so each surface (notes tab, chapter section, ...)
 * only wires up the triggers, not the dialogs and delete handlers.
 */
export const NoteModals = ({ controller, initialChapterIds }: NoteModalsProps) => (
  <>
    <NoteEditorDialog
      open={controller.editorOpen}
      onClose={controller.closeEditor}
      note={controller.editingNote}
      initialChapterIds={initialChapterIds}
    />
    <ConfirmationDialog
      open={controller.deletingNote !== null}
      title="Delete note"
      message={`Delete note "${controller.deletingNote?.title ?? ''}"? This cannot be undone.`}
      onConfirm={controller.confirmDelete}
      onClose={controller.cancelDelete}
      isLoading={controller.isDeleting}
    />
  </>
);
