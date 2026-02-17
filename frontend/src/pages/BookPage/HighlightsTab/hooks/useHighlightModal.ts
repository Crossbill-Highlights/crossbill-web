import type { Highlight } from '@/api/generated/model';
import { scrollToElementWithHighlight } from '@/components/animations/scrollUtils.ts';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useCallback, useMemo, useState } from 'react';

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
  const { highlightId: urlHighlightId } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  // Local state used when syncToUrl is false
  const [localHighlightId, setLocalHighlightId] = useState<number | undefined>();

  // URL is the source of truth when syncToUrl is true, otherwise local state
  const openHighlightId = syncToUrl ? urlHighlightId : localHighlightId;

  const updateHighlightId = useCallback(
    (newId: number | undefined, replace: boolean) => {
      if (syncToUrl) {
        navigate({
          search: (prev) => ({
            ...prev,
            highlightId: newId,
          }),
          replace,
        });
      } else {
        setLocalHighlightId(newId);
      }
    },
    [navigate, syncToUrl]
  );

  // Push to history so back button closes the modal
  const handleOpenHighlight = useCallback(
    (highlightIdToOpen: number) => {
      updateHighlightId(highlightIdToOpen, false);
    },
    [updateHighlightId]
  );

  // Replace so back after closing doesn't reopen the modal
  const handleCloseHighlight = useCallback(
    (lastViewedHighlightId?: number) => {
      updateHighlightId(undefined, true);

      if (lastViewedHighlightId && isMobile && syncToUrl) {
        scrollToElementWithHighlight(`highlight-${lastViewedHighlightId}`);
      }
    },
    [updateHighlightId, isMobile, syncToUrl]
  );

  // Replace so back goes to pre-modal state, not previous highlight
  const handleNavigateHighlight = useCallback(
    (newHighlightId: number) => {
      updateHighlightId(newHighlightId, true);
    },
    [updateHighlightId]
  );

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
