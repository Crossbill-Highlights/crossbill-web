import type { ChapterWithHighlights } from '@/api/generated/model';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useCallback, useMemo, useRef, useState } from 'react';

interface UseChapterDetailsModalOptions {
  leafChapters: ChapterWithHighlights[];
  syncToUrl?: boolean;
}

interface UseChapterDetailsModalReturn {
  selectedChapter: ChapterWithHighlights | null;
  selectedChapterIndex: number | null;
  handleChapterClick: (chapterId: number) => void;
  handleDialogClose: () => void;
  handleDialogNavigate: (newIndex: number) => void;
}

export const useChapterDetailsModal = ({
  leafChapters,
  syncToUrl = true,
}: UseChapterDetailsModalOptions): UseChapterDetailsModalReturn => {
  // strict: false so this hook works from any child route under /book/$bookId
  const search = useSearch({ strict: false }) as { chapterId?: number };
  const urlChapterId = search.chapterId;
  const navigate = useNavigate() as (opts: {
    search: (prev: Record<string, unknown>) => Record<string, unknown>;
    replace?: boolean;
  }) => Promise<void>;

  // Tracks whether modal was opened via user click (push) vs direct URL
  const wasOpenedByPush = useRef(false);

  // Local state used when syncToUrl is false
  const [localChapterId, setLocalChapterId] = useState<number | undefined>();

  // URL is the source of truth when syncToUrl is true, otherwise local state
  const activeChapterId = syncToUrl ? urlChapterId : localChapterId;

  const updateChapterId = useCallback(
    (newId: number | undefined, replace: boolean) => {
      if (syncToUrl) {
        void navigate({
          search: (prev: Record<string, unknown>) => ({ ...prev, chapterId: newId }),
          replace,
        });
      } else {
        setLocalChapterId(newId);
      }
    },
    [navigate, syncToUrl]
  );

  const selectedChapterIndex = useMemo(() => {
    if (activeChapterId === undefined) return null;
    const index = leafChapters.findIndex((ch) => ch.id === activeChapterId);
    return index !== -1 ? index : null;
  }, [leafChapters, activeChapterId]);

  const selectedChapter = useMemo(
    () => (selectedChapterIndex !== null ? (leafChapters[selectedChapterIndex] ?? null) : null),
    [leafChapters, selectedChapterIndex]
  );

  // Push to history so back button closes the dialog
  const handleChapterClick = useCallback(
    (chapterId: number) => {
      wasOpenedByPush.current = true;
      updateChapterId(chapterId, false);
    },
    [updateChapterId]
  );

  // Pop history entry if opened via push, otherwise replace
  const handleDialogClose = useCallback(() => {
    if (wasOpenedByPush.current && syncToUrl) {
      wasOpenedByPush.current = false;
      window.history.back();
    } else {
      updateChapterId(undefined, true);
    }
  }, [updateChapterId, syncToUrl]);

  // Replace so back goes to pre-dialog state, not previous chapter
  const handleDialogNavigate = useCallback(
    (newIndex: number) => {
      updateChapterId(leafChapters[newIndex].id, true);
    },
    [leafChapters, updateChapterId]
  );

  return {
    selectedChapter,
    selectedChapterIndex,
    handleChapterClick,
    handleDialogClose,
    handleDialogNavigate,
  };
};
