import { Box, Container, Typography } from '@mui/material';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Welcome to Crossbill
        </Typography>
        <Typography variant="body1">Your highlights management application</Typography>
      </Box>
    </Container>
  );
}
