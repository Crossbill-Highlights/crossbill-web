import { Box } from '@mui/material';
import { Outlet, createRootRoute } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools';

export const Route = createRootRoute({
  component: () => (
    <Box>
      <Outlet />
      <TanStackRouterDevtools />
    </Box>
  ),
});
