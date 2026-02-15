import type { ChapterWithHighlights } from '@/api/generated/model';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useCallback, useMemo, useState } from 'react';

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
  const { chapterId: urlChapterId } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  // Local state used when syncToUrl is false
  const [localChapterId, setLocalChapterId] = useState<number | undefined>();

  // URL is the source of truth when syncToUrl is true, otherwise local state
  const activeChapterId = syncToUrl ? urlChapterId : localChapterId;

  const updateChapterId = useCallback(
    (newId: number | undefined, replace: boolean) => {
      if (syncToUrl) {
        navigate({
          search: (prev) => ({
            ...prev,
            chapterId: newId,
          }),
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
      updateChapterId(chapterId, false);
    },
    [updateChapterId]
  );

  // Replace so back after closing doesn't reopen the dialog
  const handleDialogClose = useCallback(() => {
    updateChapterId(undefined, true);
  }, [updateChapterId]);

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
