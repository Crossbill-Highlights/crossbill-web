import { Box, CircularProgress } from '@mui/material';
import { Navigate, Outlet, createRootRoute, useLocation } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools';
import { AppBar } from '../components/layout/AppBar';
import { useAuth } from '../context/AuthContext';

function RootComponent() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  const isPublicPage = location.pathname === '/login' || location.pathname === '/register';

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <Box
        sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Redirect to login if not authenticated (except on public pages)
  if (!isAuthenticated && !isPublicPage) {
    return <Navigate to="/login" />;
  }

  // Redirect to home if already authenticated and on public page
  if (isAuthenticated && isPublicPage) {
    return <Navigate to="/" />;
  }

  return (
    <Box>
      {!isPublicPage && <AppBar />}
      <Outlet />
      <TanStackRouterDevtools />
    </Box>
  );
}

export const Route = createRootRoute({
  component: RootComponent,
});
