/**
 * Scrolls to an element and applies a brief highlight effect
 * @param elementId - The ID of the element to scroll to
 * @param options - Configuration options
 */
export const scrollToElementWithHighlight = (
  elementId: string,
  options: {
    behavior?: ScrollBehavior;
    block?: ScrollLogicalPosition;
    highlightColor?: string;
    highlightDuration?: number;
    delay?: number;
  } = {}
) => {
  const {
    behavior = 'auto',
    block = 'center',
    highlightColor = 'rgba(25, 118, 210, 0.08)',
    highlightDuration = 2000,
    delay = 100,
  } = options;

  setTimeout(() => {
    const element = document.getElementById(elementId);
    if (element) {
      element.scrollIntoView({ behavior, block });
      // Add a brief highlight effect
      element.style.transition = 'background-color 0.3s ease';
      element.style.backgroundColor = highlightColor;
      setTimeout(() => {
        element.style.backgroundColor = '';
      }, highlightDuration);
    }
  }, delay);
};
