import {
  ChapterListIcon,
  FlashcardsIcon,
  HighlightsIcon,
  ReadingSessionIcon,
} from '@/theme/Icons.tsx';
import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { useNavigate, useParams, useRouterState } from '@tanstack/react-router';

const getActiveTab = (pathname: string): string => {
  if (pathname.includes('/highlights')) return 'highlights';
  if (pathname.includes('/flashcards')) return 'flashcards';
  if (pathname.includes('/sessions')) return 'sessions';
  return 'structure';
};

export const MobileBottomNav = () => {
  const { bookId } = useParams({ strict: false });
  const { location } = useRouterState();
  const navigate = useNavigate();

  const activeTab = getActiveTab(location.pathname);

  const handleChange = (_event: React.SyntheticEvent, newValue: string) => {
    void navigate({
      to: `/book/$bookId/${newValue}`,
      params: { bookId: bookId! },
      replace: true,
    });
  };

  return (
    <Paper elevation={3} sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1100 }}>
      <BottomNavigation value={activeTab} onChange={handleChange} showLabels>
        <BottomNavigationAction value="structure" label="Structure" icon={<ChapterListIcon />} />
        <BottomNavigationAction value="highlights" label="Highlights" icon={<HighlightsIcon />} />
        <BottomNavigationAction value="flashcards" label="Flashcards" icon={<FlashcardsIcon />} />
        <BottomNavigationAction value="sessions" label="Sessions" icon={<ReadingSessionIcon />} />
      </BottomNavigation>
    </Paper>
  );
};
