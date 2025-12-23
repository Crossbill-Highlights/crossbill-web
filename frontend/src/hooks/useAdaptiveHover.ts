import { createAdaptiveHoverStyles, type AdaptiveHoverOptions } from '@/utils/adaptiveHover';
import { useMemo } from 'react';

/**
 * Hook that provides adaptive hover styles for touch and desktop devices.
 *
 * Returns memoized sx style objects for container and actions.
 * On touch devices, actions are always visible.
 * On desktop, actions are hidden until hover or keyboard focus.
 *
 * @param options Configuration options for adaptive hover behavior
 * @returns Object with `container` and `actions` sx props
 *
 * @example
 * ```tsx
 * const adaptiveStyles = useAdaptiveHover({ actionsClassName: 'my-actions' });
 * <Box sx={adaptiveStyles.container}>
 *   <Box className="my-actions" sx={adaptiveStyles.actions}>
 *     <IconButton>...</IconButton>
 *   </Box>
 * </Box>
 * ```
 */
export const useAdaptiveHover = (options?: AdaptiveHoverOptions) => {
  return useMemo(() => createAdaptiveHoverStyles(options), [options]);
};
