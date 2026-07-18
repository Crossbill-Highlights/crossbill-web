import { Stack, type SxProps, type Theme } from '@mui/material';
import type { ReactNode } from 'react';

interface CardListProps {
  children: ReactNode;
  sx?: SxProps<Theme>;
}

/** Unstyled `ul` stack for card lists; render each card inside an `li`. */
export const CardList = ({ children, sx }: CardListProps) => (
  <Stack
    component="ul"
    sx={[{ gap: 2, listStyle: 'none', p: 0, m: 0 }, ...(Array.isArray(sx) ? sx : [sx])]}
  >
    {children}
  </Stack>
);
