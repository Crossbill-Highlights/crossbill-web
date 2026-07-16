import { useState } from 'react';

interface VisibilityOverride {
  entityId: number;
  visible: boolean;
}

/**
 * Hook for managing visibility toggle state that auto-resets when navigating between entities
 * (e.g. highlights or notes shown in a modal).
 *
 * @param entityId - Current entity ID (used to detect navigation)
 * @param hasContent - Whether the section has content (determines default visibility)
 * @returns Object with `visible` state and `toggle` function
 *
 * @example
 * const { visible: noteVisible, toggle: toggleNote } = useVisibilityToggle(
 *   highlight.id,
 *   !!highlight.note
 * );
 */
export const useVisibilityToggle = (entityId: number, hasContent: boolean) => {
  const [override, setOverride] = useState<VisibilityOverride | null>(null);

  // Use override only if it's for the current entity, otherwise use default
  const currentOverride = override?.entityId === entityId ? override.visible : null;
  const visible = currentOverride ?? hasContent;

  const toggle = () => {
    const newVisible = currentOverride === null ? !hasContent : !currentOverride;
    setOverride({ entityId, visible: newVisible });
  };

  return { visible, toggle };
};
