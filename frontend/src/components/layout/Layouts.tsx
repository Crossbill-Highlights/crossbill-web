import { Box, Container, styled } from '@mui/material';

export const ThreeColumnLayout = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: '280px 1fr 280px',
  gap: theme.spacing(4),
  alignItems: 'start',
}));

export const ContentWithSidebar = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: '1fr 280px',
  gap: theme.spacing(4),
  alignItems: 'start',
}));

export const PageContainer = styled(Container)(({ theme }) => ({
  marginBottom: theme.spacing(10),
  [theme.breakpoints.up('xs')]: {
    marginTop: theme.spacing(3),
  },
  [theme.breakpoints.up('md')]: {
    marginTop: theme.spacing(4),
  },
}));
