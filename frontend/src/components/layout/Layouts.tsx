import { Box, Container, styled } from '@mui/material';

export const ContentWithSidebar = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: '1fr 280px',
  gap: theme.spacing(4),
  alignItems: 'start',
}));

export const PageContainer = styled(Container)(({ theme }) => ({
  paddingBottom: `calc(${theme.spacing(18)} + env(safe-area-inset-bottom))`,
  [theme.breakpoints.up('xs')]: {
    marginTop: theme.spacing(3),
  },
  [theme.breakpoints.up('md')]: {
    marginTop: theme.spacing(4),
  },
  [theme.breakpoints.up('lg')]: {
    paddingBottom: theme.spacing(5),
  },
}));
