import {
  ChapterListIcon,
  FlashcardsIcon,
  HighlightsIcon,
  ReadingSessionIcon,
} from '@/theme/Icons.tsx';
import { Box, List, ListItemButton, ListItemIcon, ListItemText } from '@mui/material';
import { Link, useMatchRoute } from '@tanstack/react-router';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/book/$bookId/structure', label: 'Structure', icon: <ChapterListIcon /> },
  { to: '/book/$bookId/highlights', label: 'Highlights', icon: <HighlightsIcon /> },
  { to: '/book/$bookId/flashcards', label: 'Flashcards', icon: <FlashcardsIcon /> },
  { to: '/book/$bookId/sessions', label: 'Sessions', icon: <ReadingSessionIcon /> },
];

interface DesktopNavLinksProps {
  bookId: string;
}

export const DesktopNavLinks = ({ bookId }: DesktopNavLinksProps) => {
  const matchRoute = useMatchRoute();

  return (
    <Box sx={{ mb: 3 }}>
      <List disablePadding>
        {NAV_ITEMS.map((item) => {
          const isActive = !!matchRoute({ to: item.to, params: { bookId } });

          return (
            <ListItemButton
              key={item.to}
              component={Link}
              to={item.to}
              params={{ bookId }}
              selected={isActive}
              sx={{
                borderRadius: 1,
                mb: 0.5,
                py: 1,
                '&.Mui-selected': {
                  backgroundColor: 'action.selected',
                  '&:hover': {
                    backgroundColor: 'action.selected',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{ minWidth: 36, color: isActive ? 'primary.main' : 'text.secondary' }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  variant: 'body2',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'primary.main' : 'text.primary',
                }}
              />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );
};
