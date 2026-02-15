import type { Highlight } from '@/api/generated/model';
import { scrollToElementWithHighlight } from '@/components/animations/scrollUtils.ts';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useCallback, useEffect, useMemo, useState } from 'react';

interface UseHighlightModalOptions {
  allHighlights: Highlight[];
  isMobile: boolean;
  syncToUrl?: boolean;
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
  syncToUrl = true,
}: UseHighlightModalOptions): UseHighlightModalReturn => {
  const { highlightId } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  const [openHighlightId, setOpenHighlightId] = useState<number | undefined>(
    syncToUrl ? highlightId : undefined
  );

  const navigateUrl = useCallback(
    (newHighlightId: number | undefined) => {
      if (!syncToUrl) return;
      navigate({
        search: (prev) => ({
          ...prev,
          highlightId: newHighlightId,
        }),
        replace: true,
      });
    },
    [navigate, syncToUrl]
  );

  const handleOpenHighlight = useCallback(
    (highlightIdToOpen: number) => {
      setOpenHighlightId(highlightIdToOpen);
      navigateUrl(highlightIdToOpen);
    },
    [navigateUrl]
  );

  const handleCloseHighlight = useCallback(
    (lastViewedHighlightId?: number) => {
      setOpenHighlightId(undefined);
      navigateUrl(undefined);

      if (lastViewedHighlightId && isMobile && syncToUrl) {
        scrollToElementWithHighlight(`highlight-${lastViewedHighlightId}`);
      }
    },
    [navigateUrl, isMobile, syncToUrl]
  );

  const handleNavigateHighlight = useCallback(
    (newHighlightId: number) => {
      setOpenHighlightId(newHighlightId);
      navigateUrl(newHighlightId);
    },
    [navigateUrl]
  );

  // Sync modal state when URL changes (e.g., browser back/forward)
  useEffect(() => {
    if (syncToUrl) {
      setOpenHighlightId(highlightId);
    }
  }, [highlightId, syncToUrl]);

  const currentHighlightIndex = useMemo(() => {
    if (!openHighlightId) return -1;
    return allHighlights.findIndex((h) => h.id === openHighlightId);
  }, [allHighlights, openHighlightId]);

  const currentHighlight = useMemo(() => {
    if (currentHighlightIndex === -1) return null;
    return allHighlights[currentHighlightIndex];
  }, [allHighlights, currentHighlightIndex]);

  const handleModalNavigate = useCallback(
    (newIndex: number) => {
      const newHighlight = allHighlights[newIndex]!;
      handleNavigateHighlight(newHighlight.id);
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
