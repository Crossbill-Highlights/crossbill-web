import type { NoteWithLinks } from '@/api/generated/model';
import { getGetNoteApiV1NotesNoteIdGetQueryKey } from '@/api/generated/notes/notes.ts';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useCallback, useRef, useState } from 'react';

interface UseNoteModalsOptions {
  /**
   * Sync the open note to the `noteId` URL search param so the detail modal is
   * shareable/deep-linkable (like `?highlightId=`). Defaults to true. Nested
   * surfaces that already own the URL (e.g. the chapter dialog) pass false to
   * keep the open note in local state instead.
   */
  syncToUrl?: boolean;
}

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
  viewingNoteId: number | null;
  closeView: () => void;
}

export const useNoteModals = (options: UseNoteModalsOptions = {}): NoteModalsController => {
  const { syncToUrl = true } = options;
  const queryClient = useQueryClient();

  const [editorOpen, setEditorOpen] = useState(false);

  // strict: false so this hook works from any child route under /book/$bookId
  const search = useSearch({ strict: false }) as { noteId?: number };
  const navigate = useNavigate() as (opts: {
    search: (prev: Record<string, unknown>) => Record<string, unknown>;
    replace?: boolean;
  }) => Promise<void>;

  // Local state used when syncToUrl is false (e.g. inside the chapter dialog).
  const [localNoteId, setLocalNoteId] = useState<number | null>(null);
  // Tracks whether the modal was opened via user click (push) vs a direct URL.
  const wasOpenedByPush = useRef(false);

  const viewingNoteId = syncToUrl ? (search.noteId ?? null) : localNoteId;

  const setNoteId = useCallback(
    (noteId: number | undefined, replace: boolean) => {
      if (syncToUrl) {
        void navigate({
          search: (prev) => ({ ...prev, noteId }),
          replace,
        });
      } else {
        setLocalNoteId(noteId ?? null);
      }
    },
    [navigate, syncToUrl]
  );

  const openView = useCallback(
    (note: NoteWithLinks) => {
      // Seed the detail query so the modal renders instantly instead of
      // flashing a spinner while the GET resolves.
      queryClient.setQueryData(getGetNoteApiV1NotesNoteIdGetQueryKey(note.id), note);
      wasOpenedByPush.current = true;
      // Push a history entry so the back button closes the modal.
      setNoteId(note.id, false);
    },
    [queryClient, setNoteId]
  );

  const closeView = useCallback(() => {
    if (wasOpenedByPush.current && syncToUrl) {
      wasOpenedByPush.current = false;
      window.history.back();
    } else {
      setNoteId(undefined, true);
    }
  }, [setNoteId, syncToUrl]);

  return {
    openCreate: () => setEditorOpen(true),
    openView,
    editorOpen,
    closeEditor: () => setEditorOpen(false),
    viewingNoteId,
    closeView,
  };
};
