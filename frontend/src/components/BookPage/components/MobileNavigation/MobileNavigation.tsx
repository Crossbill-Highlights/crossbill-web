import { BookDetails, Bookmark, Highlight } from '@/api/generated/model';
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
import { BookmarkList } from '../BookmarkList';
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

interface BookmarksDrawerContentProps {
  bookmarks: Bookmark[];
  allHighlights: Highlight[];
  onBookmarkClick: (highlightId: number) => void;
}

const BookmarksDrawerContent = ({
  bookmarks,
  allHighlights,
  onBookmarkClick,
}: BookmarksDrawerContentProps) => {
  return (
    <Box>
      <BookmarkList
        bookmarks={bookmarks || []}
        allHighlights={allHighlights}
        onBookmarkClick={onBookmarkClick}
      />
    </Box>
  );
};

type MobileNavigationProps = TagsDrawerContentProps & BookmarksDrawerContentProps;
type DrawerContentType = 'tags' | 'bookmarks';

export const MobileNavigation = ({
  book,
  selectedTag,
  onTagClick,
  bookmarks,
  allHighlights,
  onBookmarkClick,
}: MobileNavigationProps) => {
  const [drawerIsOpen, setDrawerState] = useState(false);
  const [drawerContent, setDrawerContent] = useState<DrawerContentType>('tags');

  const getDrawerContent = (type: DrawerContentType) => {
    if (type === 'tags') {
      return (
        <TagsDrawerContent
          book={book}
          selectedTag={selectedTag}
          onTagClick={(data) => {
            onTagClick(data);
            setDrawerState(false);
          }}
        />
      );
    }
    if (type === 'bookmarks') {
      return (
        <BookmarksDrawerContent
          bookmarks={bookmarks}
          allHighlights={allHighlights}
          onBookmarkClick={(data) => {
            setDrawerState(false);
            onBookmarkClick(data);
          }}
        />
      );
    }
  };

  return (
    <>
      <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0 }} elevation={3}>
        <BottomNavigation
          showLabels
          onChange={() => {
            setDrawerState(true);
          }}
        >
          <BottomNavigationAction
            label="Tags"
            icon={<TagIcon />}
            onClick={() => {
              setDrawerContent('tags');
            }}
          />
          <BottomNavigationAction
            label="Bookmarks"
            icon={<BookmarkIcon />}
            onClick={() => {
              setDrawerContent('bookmarks');
            }}
          />
          <BottomNavigationAction label="Chapters" icon={<ListIcon />} />
        </BottomNavigation>
      </Paper>
      <BottomDrawer
        isOpen={drawerIsOpen}
        onClose={() => setDrawerState(false)}
        content={getDrawerContent(drawerContent)}
      />
    </>
  );
};
