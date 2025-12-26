import { BookDetails, Bookmark, Highlight, HighlightTagInBook } from '@/api/generated/model';
import { ChapterData } from '@/components/BookPage/components/HighlightsTab/ChapterList.tsx';
import { ChapterNav } from '@/components/BookPage/components/HighlightsTab/ChapterNav.tsx';
import {
  BookmarkFilledIcon,
  ChapterListIcon,
  CloseIcon,
  TagIcon,
} from '@/components/common/Icons.tsx';
import {
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Drawer,
  IconButton,
  Paper,
  Typography,
} from '@mui/material';
import { motion } from 'motion/react';
import { useState } from 'react';
import { BookmarkList } from './BookmarkList.tsx';
import { HighlightTags } from './HighlightTags.tsx';

const BottomDrawer = ({
  isOpen,
  onClose,
  content,
  title,
}: {
  isOpen: boolean;
  onClose: () => void;
  content: React.ReactNode;
  title: React.ReactNode;
}) => {
  return (
    <Drawer anchor="bottom" open={isOpen} onClose={onClose}>
      <Box
        sx={{
          padding: 2,
          paddingBottom: 6,
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          {title}
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
  displayTags?: HighlightTagInBook[];
  currentTab: 'highlights' | 'flashcards';
}

const TagsDrawerContent = ({
  book,
  selectedTag,
  onTagClick,
  displayTags,
  currentTab,
}: TagsDrawerContentProps) => {
  return (
    <Box>
      <HighlightTags
        tags={displayTags || book.highlight_tags || []}
        tagGroups={book.highlight_tag_groups || []}
        bookId={book.id}
        selectedTag={selectedTag}
        onTagClick={onTagClick}
        hideTitle={true}
        hideEmptyGroups={currentTab === 'flashcards'}
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
        hideTitle={true}
      />
    </Box>
  );
};

interface ChaptersDrawerContentProps {
  chapters: ChapterData[];
  onChapterClick: (chapterId: number | string) => void;
}

const ChaptersDrawerContent = ({ chapters, onChapterClick }: ChaptersDrawerContentProps) => {
  return (
    <Box>
      <ChapterNav chapters={chapters} onChapterClick={onChapterClick} hideTitle={true} />
    </Box>
  );
};

type MobileNavigationProps = { currentTab: 'highlights' | 'flashcards' } & TagsDrawerContentProps &
  BookmarksDrawerContentProps &
  ChaptersDrawerContentProps;
type DrawerContentType = 'tags' | 'bookmarks' | 'chapters';

export const MobileNavigation = ({
  book,
  selectedTag,
  onTagClick,
  bookmarks,
  allHighlights,
  onBookmarkClick,
  chapters,
  onChapterClick,
  displayTags,
  currentTab,
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
          displayTags={displayTags}
          currentTab={currentTab}
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
    if (type === 'chapters') {
      return (
        <ChaptersDrawerContent
          chapters={chapters}
          onChapterClick={(data) => {
            setDrawerState(false);
            onChapterClick(data);
          }}
        />
      );
    }
  };

  const getDrawerTitle = (type: DrawerContentType): React.ReactNode => {
    const config: Record<DrawerContentType, { icon: React.ReactNode; text: string }> = {
      tags: { icon: <TagIcon />, text: 'Tags' },
      bookmarks: { icon: <BookmarkFilledIcon />, text: 'Bookmarks' },
      chapters: { icon: <ChapterListIcon />, text: 'Chapters' },
    };

    const { icon, text } = config[type];

    return (
      <Box display="flex" alignItems="center" gap={1}>
        {icon}
        <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
          {text}
        </Typography>
      </Box>
    );
  };

  return (
    <>
      <motion.div
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        style={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1100 }}
      >
        <Paper elevation={3}>
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
              icon={<BookmarkFilledIcon />}
              onClick={() => {
                setDrawerContent('bookmarks');
              }}
            />
            <BottomNavigationAction
              label="Chapters"
              icon={<ChapterListIcon />}
              onClick={() => {
                setDrawerContent('chapters');
              }}
            />
          </BottomNavigation>
        </Paper>
      </motion.div>
      <BottomDrawer
        isOpen={drawerIsOpen}
        onClose={() => setDrawerState(false)}
        title={getDrawerTitle(drawerContent)}
        content={getDrawerContent(drawerContent)}
      />
    </>
  );
};
