import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
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
}

export const ScrollToTopButton = ({
  scrollThreshold = 300,
  scrollBehavior = 'smooth',
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
          bottom: { xs: 80, lg: 24 },
          right: 24,
          zIndex: 1000,
        }}
      >
        <KeyboardArrowUpIcon />
      </Fab>
    </Zoom>
  );
};
