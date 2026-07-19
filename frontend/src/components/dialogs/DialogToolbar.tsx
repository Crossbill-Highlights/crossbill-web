import { Box, type SxProps, type Theme } from '@mui/material';
import type { ReactNode } from 'react';

interface DialogToolbarProps {
  children: ReactNode;
  sx?: SxProps<Theme>;
}

/** Right-aligned action row used by the entity detail modals' toolbars. */
export const DialogToolbar = ({ children, sx }: DialogToolbarProps) => (
  <Box
    sx={[
      { display: 'flex', justifyContent: 'flex-end', gap: 1 },
      ...(Array.isArray(sx) ? sx : [sx]),
    ]}
  >
    {children}
  </Box>
);
