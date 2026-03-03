import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { useNavigate, useParams, useRouterState } from '@tanstack/react-router';
import { BOOK_PAGE_ROUTES } from './bookPageRoutes.ts';

const getActivePage = (pathname: string): string => {
  const match = BOOK_PAGE_ROUTES.find((route) => pathname.includes(`/${route.segment}`));
  return match?.segment ?? 'structure';
};

export const MobileBottomNav = () => {
  const { bookId } = useParams({ strict: false });
  const { location } = useRouterState();
  const navigate = useNavigate();

  const activePage = getActivePage(location.pathname);

  const handleChange = (_event: React.SyntheticEvent, newValue: string) => {
    void navigate({
      to: `/book/$bookId/${newValue}`,
      params: { bookId: bookId! },
      replace: true,
    });
  };

  return (
    <Paper elevation={3} sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1100 }}>
      <BottomNavigation value={activePage} onChange={handleChange} showLabels>
        {BOOK_PAGE_ROUTES.map((route) => {
          const Icon = route.icon;
          return (
            <BottomNavigationAction
              key={route.segment}
              value={route.segment}
              label={route.label}
              icon={<Icon />}
            />
          );
        })}
      </BottomNavigation>
    </Paper>
  );
};
