import { useCallback, useEffect } from 'react';
import { useSwipeable } from 'react-swipeable';

interface UseHighlightNavigationOptions {
  open: boolean;
  currentIndex: number;
  totalCount: number;
  onNavigate?: (newIndex: number) => void;
}

export const useHighlightNavigation = ({
  open,
  currentIndex,
  totalCount,
  onNavigate,
}: UseHighlightNavigationOptions) => {
  const hasNavigation = totalCount > 1 && onNavigate;
  const hasPrevious = hasNavigation && currentIndex > 0;
  const hasNext = hasNavigation && currentIndex < totalCount - 1;

  const handlePrevious = useCallback(() => {
    if (hasPrevious) {
      onNavigate!(currentIndex - 1);
    }
  }, [currentIndex, hasPrevious, onNavigate]);

  const handleNext = useCallback(() => {
    if (hasNext) {
      onNavigate!(currentIndex + 1);
    }
  }, [currentIndex, hasNext, onNavigate]);

  // Keyboard navigation
  useEffect(() => {
    if (!open || !hasNavigation) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't navigate when user is typing in an input field
      const target = e.target as HTMLElement;
      const isEditableElement =
        target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

      if (isEditableElement) return;

      if (e.key === 'ArrowLeft' && hasPrevious) {
        e.preventDefault();
        handlePrevious();
      } else if (e.key === 'ArrowRight' && hasNext) {
        e.preventDefault();
        handleNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext]);

  // Swipe navigation
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => {
      if (hasNext) handleNext();
    },
    onSwipedRight: () => {
      if (hasPrevious) handlePrevious();
    },
    swipeDuration: 500,
    preventScrollOnSwipe: false,
  });

  return {
    hasNavigation,
    hasPrevious,
    hasNext,
    handlePrevious,
    handleNext,
    swipeHandlers,
  };
};
