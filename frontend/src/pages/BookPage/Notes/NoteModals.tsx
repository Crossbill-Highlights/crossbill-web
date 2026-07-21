import type { Note } from '@/api/generated/model';

import { NoteEditorDialog } from './NoteEditorDialog';
import { NoteViewModal } from './NoteViewModal';
import type { NoteModalsController } from './hooks/useNoteModals';

interface NoteModalsProps {
  controller: NoteModalsController;
  /** Pre-link created notes to these chapters (e.g. from the chapter section). */
  initialChapterIds?: number[];
  /** Pre-link created notes to these highlights (e.g. from the highlight modal). */
  initialHighlightIds?: number[];
  /** Called with the created note after a successful create (not on update). */
  onCreated?: (note: Note) => void;
}

/**
 * Renders the note create editor and the note detail modal for a `useNoteModals`
 * controller, so each surface (notes tab, chapter section, ...) only wires up the
 * triggers, not the dialogs. Editing/deleting an existing note lives inside
 * `NoteViewModal`.
 *
 * Prev/next navigation is forwarded only when the controller knows the viewed
 * note's position in its `allNotes` list — a deep link to a note filtered out
 * of the current list still opens, just without navigation.
 */
export const NoteModals = ({
  controller,
  initialChapterIds,
  initialHighlightIds,
  onCreated,
}: NoteModalsProps) => {
  const hasNavigation = controller.currentNoteIndex >= 0 && controller.totalCount > 1;

  return (
    <>
      <NoteEditorDialog
        open={controller.editorOpen}
        onClose={controller.closeEditor}
        initialChapterIds={initialChapterIds}
        initialHighlightIds={initialHighlightIds}
        onCreated={onCreated}
      />
      {controller.viewingNoteId !== null && (
        <NoteViewModal
          noteId={controller.viewingNoteId}
          onClose={controller.closeView}
          currentIndex={hasNavigation ? controller.currentNoteIndex : undefined}
          totalCount={hasNavigation ? controller.totalCount : undefined}
          onNavigate={hasNavigation ? controller.handleModalNavigate : undefined}
        />
      )}
    </>
  );
};
