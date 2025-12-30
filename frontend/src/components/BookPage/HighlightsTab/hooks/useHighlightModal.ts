import type { Highlight } from '@/api/generated/model';
import { scrollToElementWithHighlight } from '@/components/common/animations/scrollUtils.ts';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useCallback, useEffect, useMemo, useState } from 'react';

interface UseHighlightModalOptions {
  allHighlights: Highlight[];
  isMobile: boolean;
}

interface UseHighlightModalReturn {
  openHighlightId: number | undefined;
  currentHighlight: Highlight | null;
  currentHighlightIndex: number;
  handleOpenHighlight: (highlightId: number) => void;
  handleCloseHighlight: (lastViewedHighlightId?: number) => void;
  handleNavigateHighlight: (newHighlightId: number) => void;
  handleModalNavigate: (newIndex: number) => void;
}

export const useHighlightModal = ({
  allHighlights,
  isMobile,
}: UseHighlightModalOptions): UseHighlightModalReturn => {
  const { highlightId } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  // Modal state for highlight viewing - synced with URL
  const [openHighlightId, setOpenHighlightId] = useState<number | undefined>(highlightId);

  // Handler to open a highlight modal - updates URL
  const handleOpenHighlight = useCallback(
    (highlightIdToOpen: number) => {
      setOpenHighlightId(highlightIdToOpen);
      navigate({
        search: (prev) => ({
          ...prev,
          highlightId: highlightIdToOpen,
        }),
        replace: true,
      });
    },
    [navigate]
  );

  // Handler to close the highlight modal - removes highlightId from URL
  const handleCloseHighlight = useCallback(
    (lastViewedHighlightId?: number) => {
      setOpenHighlightId(undefined);
      navigate({
        search: (prev) => ({
          ...prev,
          highlightId: undefined,
        }),
        replace: true,
      });

      // Scroll to the last viewed highlight (mobile only)
      if (lastViewedHighlightId && isMobile) {
        scrollToElementWithHighlight(`highlight-${lastViewedHighlightId}`);
      }
    },
    [navigate, isMobile]
  );

  // Handler to navigate between highlights - updates URL
  const handleNavigateHighlight = useCallback(
    (newHighlightId: number) => {
      setOpenHighlightId(newHighlightId);
      navigate({
        search: (prev) => ({
          ...prev,
          highlightId: newHighlightId,
        }),
        replace: true,
      });
    },
    [navigate]
  );

  // Sync modal state when URL changes (e.g., browser back/forward)
  useEffect(() => {
    setOpenHighlightId(highlightId);
  }, [highlightId]);

  // Find the current highlight and its index for the modal
  const currentHighlightIndex = useMemo(() => {
    if (!openHighlightId) return -1;
    return allHighlights.findIndex((h) => h.id === openHighlightId);
  }, [allHighlights, openHighlightId]);

  const currentHighlight = useMemo(() => {
    if (currentHighlightIndex === -1) return null;
    return allHighlights[currentHighlightIndex];
  }, [allHighlights, currentHighlightIndex]);

  // Handler for modal navigation - converts index to highlight ID
  const handleModalNavigate = useCallback(
    (newIndex: number) => {
      const newHighlight = allHighlights[newIndex];
      if (newHighlight) {
        handleNavigateHighlight(newHighlight.id);
      }
    },
    [allHighlights, handleNavigateHighlight]
  );

  return {
    openHighlightId,
    currentHighlight,
    currentHighlightIndex,
    handleOpenHighlight,
    handleCloseHighlight,
    handleNavigateHighlight,
    handleModalNavigate,
  };
};
