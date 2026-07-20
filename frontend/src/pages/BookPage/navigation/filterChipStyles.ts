import type { SxProps, Theme } from '@mui/material';

export const filterChipBaseSx = {
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  py: 0.25,
  px: 0.5,
} satisfies SxProps<Theme>;

export const filterChipOutlinedSx = {
  borderColor: 'divider',
  '&:hover': {
    bgcolor: 'action.hover',
    borderColor: 'secondary.light',
    transform: 'translateY(-1px)',
  },
} satisfies SxProps<Theme>;
