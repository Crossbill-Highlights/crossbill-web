import type { ChapterWithHighlights } from '@/api/generated/model';
import { useCallback, useMemo, useState } from 'react';

interface UseChapterDetailsModalOptions {
  leafChapters: ChapterWithHighlights[];
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
}: UseChapterDetailsModalOptions): UseChapterDetailsModalReturn => {
  const [selectedChapterIndex, setSelectedChapterIndex] = useState<number | null>(null);

  const selectedChapter = useMemo(
    () => (selectedChapterIndex !== null ? (leafChapters[selectedChapterIndex] ?? null) : null),
    [leafChapters, selectedChapterIndex]
  );

  const handleChapterClick = useCallback(
    (chapterId: number) => {
      const index = leafChapters.findIndex((ch) => ch.id === chapterId);
      if (index !== -1) setSelectedChapterIndex(index);
    },
    [leafChapters]
  );

  const handleDialogClose = useCallback(() => {
    setSelectedChapterIndex(null);
  }, []);

  const handleDialogNavigate = useCallback((newIndex: number) => {
    setSelectedChapterIndex(newIndex);
  }, []);

  return {
    selectedChapter,
    selectedChapterIndex,
    handleChapterClick,
    handleDialogClose,
    handleDialogNavigate,
  };
};
