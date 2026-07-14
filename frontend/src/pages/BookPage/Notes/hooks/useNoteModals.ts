import type { NoteWithLinks } from '@/api/generated/model';
import { getGetNoteApiV1NotesNoteIdGetQueryKey } from '@/api/generated/notes/notes.ts';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useCallback, useRef, useState } from 'react';

interface UseNoteModalsOptions {
  syncToUrl?: boolean;
}

export interface NoteModalsController {
  openCreate: () => void;
  openView: (note: NoteWithLinks) => void;
  editorOpen: boolean;
  closeEditor: () => void;
  viewingNoteId: number | null;
  closeView: () => void;
}

export const useNoteModals = (options: UseNoteModalsOptions = {}): NoteModalsController => {
  const { syncToUrl = true } = options;
  const queryClient = useQueryClient();

  const [editorOpen, setEditorOpen] = useState(false);

  const search = useSearch({ strict: false }) as { noteId?: number };
  const navigate = useNavigate() as (opts: {
    search: (prev: Record<string, unknown>) => Record<string, unknown>;
    replace?: boolean;
  }) => Promise<void>;

  const [localNoteId, setLocalNoteId] = useState<number | null>(null);
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
      queryClient.setQueryData(getGetNoteApiV1NotesNoteIdGetQueryKey(note.id), note);
      wasOpenedByPush.current = true;
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
