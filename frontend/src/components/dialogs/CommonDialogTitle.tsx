import { Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface CommonDialogTitleProps {
  children: ReactNode;
}

export const CommonDialogTitle = ({ children }: CommonDialogTitleProps) => (
  <Typography
    variant="h6"
    component="span"
    sx={{
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      maxWidth: { xs: 'calc(100vw - 120px)', sm: 'calc(100vw - 200px)', md: '600px' },
      display: 'block',
    }}
  >
    {children}
  </Typography>
);
