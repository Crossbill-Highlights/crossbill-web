import { Close as CloseIcon } from '@mui/icons-material';
import {
  Box,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import type { ReactNode } from 'react';

interface CommonDialogProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  children: ReactNode;
  footerActions?: ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
}

/**
 * Common dialog component with standard structure:
 * - Header with title and close button
 * - Scrollable content area
 * - Optional footer with action buttons
 * - Mobile-friendly with fullscreen mode on small screens
 * - Safe-area padding for devices with rounded corners (iPhone)
 */
export const CommonDialog = ({
  open,
  onClose,
  title,
  children,
  footerActions,
  maxWidth = 'sm',
  isLoading = false,
}: CommonDialogProps) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth={maxWidth}
      fullWidth
      fullScreen={fullScreen}
      scroll="paper"
      slotProps={{
        backdrop: {
          sx: {
            // Prevent touch scrolling on backdrop
            touchAction: 'none',
          },
        },
      }}
      sx={{
        // Prevent overscroll behavior on mobile
        '& .MuiDialog-container': {
          overscrollBehavior: 'contain',
          // Prevent touch scrolling from affecting content behind modal
          touchAction: 'none',
        },
        // Ensure dialog paper prevents touch scrolling propagation
        '& .MuiDialog-paper': {
          overscrollBehavior: 'contain',
        },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          {title}
          <IconButton
            edge="end"
            color="inherit"
            onClick={onClose}
            aria-label="close"
            disabled={isLoading}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>{children}</DialogContent>

      {footerActions && (
        <DialogActions
          sx={{
            justifyContent: 'space-between',
            // Add safe-area padding for iPhone rounded corners
            // Uses max() to ensure minimum 16px padding, but respects safe-area-inset-bottom
            pb: 'max(16px, calc(16px + env(safe-area-inset-bottom)))',
            pr: 2,
            pl: 2,
          }}
        >
          {footerActions}
        </DialogActions>
      )}
    </Dialog>
  );
};
