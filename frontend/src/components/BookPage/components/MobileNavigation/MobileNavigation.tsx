import { BookDetails } from '@/api/generated/model';
import {
  Bookmark as BookmarkIcon,
  Close as CloseIcon,
  List as ListIcon,
  LocalOffer as TagIcon,
} from '@mui/icons-material';
import {
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Drawer,
  IconButton,
  Paper,
} from '@mui/material';
import { useState } from 'react';
import { HighlightTags } from '../HighlightTags';

const BottomDrawer = ({
  isOpen,
  onClose,
  content,
}: {
  isOpen: boolean;
  onClose: () => void;
  content: React.ReactNode;
}) => {
  return (
    <Drawer anchor="bottom" open={isOpen} onClose={onClose}>
      <Box
        sx={{
          padding: 2,
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="end" sx={{ mt: -1, mb: 2 }}>
          <IconButton edge="end" color="inherit" onClick={onClose} aria-label="close">
            <CloseIcon />
          </IconButton>
        </Box>
        {content}
      </Box>
    </Drawer>
  );
};

interface TagsDrawerContentProps {
  book: BookDetails;
  selectedTag?: number | null;
  onTagClick: (tagId: number | null) => void;
}

const TagsDrawerContent = ({ book, selectedTag, onTagClick }: TagsDrawerContentProps) => {
  return (
    <Box>
      <HighlightTags
        tags={book.highlight_tags || []}
        tagGroups={book.highlight_tag_groups || []}
        bookId={book.id}
        selectedTag={selectedTag}
        onTagClick={onTagClick}
      />
    </Box>
  );
};

type MobileNavigationProps = {} & TagsDrawerContentProps;

export const MobileNavigation = ({ book, selectedTag, onTagClick }: MobileNavigationProps) => {
  const [drawerIsOpen, setDrawerState] = useState(false);
  return (
    <>
      <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0 }} elevation={3}>
        <BottomNavigation
          showLabels
          onChange={() => {
            setDrawerState(true);
          }}
        >
          <BottomNavigationAction label="Tags" icon={<TagIcon />} />
          <BottomNavigationAction label="Bookmarks" icon={<BookmarkIcon />} />
          <BottomNavigationAction label="Chapters" icon={<ListIcon />} />
        </BottomNavigation>
      </Paper>
      <BottomDrawer
        isOpen={drawerIsOpen}
        onClose={() => setDrawerState(false)}
        content={
          <TagsDrawerContent book={book} selectedTag={selectedTag} onTagClick={onTagClick} />
        }
      />
    </>
  );
};
