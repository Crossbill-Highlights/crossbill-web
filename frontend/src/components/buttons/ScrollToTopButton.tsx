import { ScrollToTopIcon } from '@/theme/Icons.tsx';
import { Fab, Zoom } from '@mui/material';
import { useEffect, useState } from 'react';

interface ScrollToTopButtonProps {
  /**
   * The scroll threshold in pixels after which the button appears.
   * @default 300
   */
  scrollThreshold?: number;
  /**
   * The scroll behavior when clicking the button.
   * @default 'smooth'
   */
  scrollBehavior?: ScrollBehavior;
  /**
   * Extra pixels to add to the bottom position (e.g. to stack above a floating FAB).
   * @default 0
   */
  bottomOffset?: number;
}

export const ScrollToTopButton = ({
  scrollThreshold = 300,
  scrollBehavior = 'smooth',
  bottomOffset = 0,
}: ScrollToTopButtonProps) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrolled = window.scrollY > scrollThreshold;
      setIsVisible(scrolled);
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll();

    // Cleanup
    return () => window.removeEventListener('scroll', handleScroll);
  }, [scrollThreshold]);

  const handleClick = () => {
    window.scrollTo({
      top: 0,
      behavior: scrollBehavior,
    });
  };

  return (
    <Zoom in={isVisible}>
      <Fab
        size="small"
        color="primary"
        aria-label="scroll to top"
        onClick={handleClick}
        sx={{
          position: 'fixed',
          bottom: { xs: 80 + bottomOffset, lg: 24 },
          right: 24,
          zIndex: 1000,
        }}
      >
        <ScrollToTopIcon />
      </Fab>
    </Zoom>
  );
};
