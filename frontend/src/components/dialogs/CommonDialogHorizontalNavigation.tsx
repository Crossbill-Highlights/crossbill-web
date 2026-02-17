import { ArrowBackIcon, ArrowForwardIcon } from '@/theme/Icons.tsx';
import { Box, Button, IconButton } from '@mui/material';
import type { ReactNode } from 'react';
import type { SwipeableHandlers } from 'react-swipeable';

interface CommonDialogHorizontalNavigationProps {
  hasNavigation: boolean | undefined | ((newIndex: number) => void);
  hasPrevious: boolean | undefined | ((newIndex: number) => void);
  hasNext: boolean | undefined | ((newIndex: number) => void);
  onPrevious: () => void;
  onNext: () => void;
  swipeHandlers: SwipeableHandlers;
  disabled?: boolean;
  children: ReactNode;
}

export const CommonDialogHorizontalNavigation = ({
  hasNavigation,
  hasPrevious,
  hasNext,
  onPrevious,
  onNext,
  swipeHandlers,
  disabled,
  children,
}: CommonDialogHorizontalNavigationProps) => (
  <>
    {/* Desktop Layout: Navigation buttons on sides */}
    <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'center', gap: 2 }}>
      {hasNavigation && (
        <IconButton
          onClick={onPrevious}
          disabled={!hasPrevious || disabled}
          sx={{
            flexShrink: 0,
            visibility: hasPrevious ? 'visible' : 'hidden',
          }}
          aria-label="Previous"
        >
          <ArrowBackIcon />
        </IconButton>
      )}

      <Box display="flex" flexDirection="column" gap={3} flex={1} {...swipeHandlers}>
        {children}
      </Box>

      {hasNavigation && (
        <IconButton
          onClick={onNext}
          disabled={!hasNext || disabled}
          sx={{
            flexShrink: 0,
            visibility: hasNext ? 'visible' : 'hidden',
          }}
          aria-label="Next"
        >
          <ArrowForwardIcon />
        </IconButton>
      )}
    </Box>

    {/* Mobile Layout: Navigation buttons below */}
    <Box
      sx={{ display: { xs: 'flex', sm: 'none' }, flexDirection: 'column', gap: 3 }}
      {...swipeHandlers}
    >
      {children}

      {hasNavigation && (
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, pt: 1 }}>
          <Button
            onClick={onPrevious}
            disabled={!hasPrevious || disabled}
            startIcon={<ArrowBackIcon />}
            variant="outlined"
            sx={{ flex: 1, maxWidth: '200px' }}
          >
            Previous
          </Button>
          <Button
            onClick={onNext}
            disabled={!hasNext || disabled}
            endIcon={<ArrowForwardIcon />}
            variant="outlined"
            sx={{ flex: 1, maxWidth: '200px' }}
          >
            Next
          </Button>
        </Box>
      )}
    </Box>
  </>
);
