import { useState } from 'react';

interface VisibilityOverride {
  highlightId: number;
  visible: boolean;
}

/**
 * Hook for managing visibility toggle state that auto-resets when navigating between highlights.
 *
 * @param highlightId - Current highlight ID (used to detect navigation)
 * @param hasContent - Whether the section has content (determines default visibility)
 * @returns Object with `visible` state and `toggle` function
 *
 * @example
 * const { visible: noteVisible, toggle: toggleNote } = useVisibilityToggle(
 *   highlight.id,
 *   !!highlight.note
 * );
 */
export const useVisibilityToggle = (highlightId: number, hasContent: boolean) => {
  const [override, setOverride] = useState<VisibilityOverride | null>(null);

  // Use override only if it's for the current highlight, otherwise use default
  const currentOverride = override?.highlightId === highlightId ? override.visible : null;
  const visible = currentOverride ?? hasContent;

  const toggle = () => {
    const newVisible = currentOverride === null ? !hasContent : !currentOverride;
    setOverride({ highlightId, visible: newVisible });
  };

  return { visible, toggle };
};
