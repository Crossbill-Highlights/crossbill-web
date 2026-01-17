import { CardActionArea, styled } from '@mui/material';

export const HoverableCardActionArea = styled(CardActionArea)(({ theme }) => ({
  borderLeft: `3px solid transparent`,
  borderRadius: theme.spacing(0.75),
  transition: 'all 0.2s ease',
  cursor: 'pointer',
  '@media (hover: hover)': {
    '&:hover': {
      backgroundColor: theme.palette.action.hover,
      borderLeftColor: theme.palette.primary.main,
      boxShadow: theme.shadows[2],
    },
  },
}));
