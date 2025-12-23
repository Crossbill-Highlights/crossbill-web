import {
  Bookmark as BookmarkIcon,
  List as ListIcon,
  LocalOffer as TagIcon,
} from '@mui/icons-material';
import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';

export const MobileNavigation = () => {
  return (
    <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0 }} elevation={3}>
      <BottomNavigation showLabels>
        <BottomNavigationAction label="Tags" icon={<TagIcon />} />
        <BottomNavigationAction label="Bookmarks" icon={<BookmarkIcon />} />
        <BottomNavigationAction label="Chapters" icon={<ListIcon />} />
      </BottomNavigation>
    </Paper>
  );
};
