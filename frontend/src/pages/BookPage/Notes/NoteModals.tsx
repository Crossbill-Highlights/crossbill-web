import { NoteEditorDialog } from './NoteEditorDialog';
import { NoteViewModal } from './NoteViewModal';
import type { NoteModalsController } from './hooks/useNoteModals';

interface NoteModalsProps {
  controller: NoteModalsController;
  /** Pre-link created notes to these chapters (e.g. from the chapter section). */
  initialChapterIds?: number[];
}

/**
 * Renders the note create editor and the note detail modal for a `useNoteModals`
 * controller, so each surface (notes tab, chapter section, ...) only wires up the
 * triggers, not the dialogs. Editing/deleting an existing note lives inside
 * `NoteViewModal`.
 */
export const NoteModals = ({ controller, initialChapterIds }: NoteModalsProps) => (
  <>
    <NoteEditorDialog
      open={controller.editorOpen}
      onClose={controller.closeEditor}
      initialChapterIds={initialChapterIds}
    />
    {controller.viewingNoteId !== null && (
      <NoteViewModal
        key={controller.viewingNoteId}
        noteId={controller.viewingNoteId}
        onClose={controller.closeView}
      />
    )}
  </>
);
