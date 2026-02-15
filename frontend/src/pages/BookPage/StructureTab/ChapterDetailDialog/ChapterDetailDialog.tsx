import type {
  Bookmark,
  ChapterPrereadingResponse,
  ChapterWithHighlights,
  HighlightTagInBook,
  PositionResponse,
} from '@/api/generated/model';
import { FadeInOut } from '@/components/animations/FadeInOut.tsx';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { ProgressBar } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/components/ProgressBar.tsx';
import { useHighlightNavigation } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/hooks/useHighlightNavigation.ts';
import { ArrowBackIcon, ArrowForwardIcon } from '@/theme/Icons.tsx';
import { Box, Button, IconButton, Typography } from '@mui/material';
import { FlashcardsSection } from './FlashcardsSection.tsx';
import { HighlightsSection } from './HighlightsSection.tsx';
import { PrereadingSection } from './PrereadingSection.tsx';

interface ChapterDetailDialogProps {
  open: boolean;
  onClose: () => void;
  chapter: ChapterWithHighlights;
  bookId: number;
  allLeafChapters: ChapterWithHighlights[];
  currentIndex: number;
  onNavigate: (newIndex: number) => void;
  prereadingByChapterId: Record<number, ChapterPrereadingResponse>;
  bookmarksByHighlightId: Record<number, Bookmark>;
  availableTags: HighlightTagInBook[];
  readingPosition?: PositionResponse | null;
}

export const ChapterDetailDialog = ({
  open,
  onClose,
  chapter,
  bookId,
  allLeafChapters,
  currentIndex,
  onNavigate,
  prereadingByChapterId,
  bookmarksByHighlightId,
  availableTags,
  readingPosition,
}: ChapterDetailDialogProps) => {
  const { hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext, swipeHandlers } =
    useHighlightNavigation({
      open,
      currentIndex,
      totalCount: allLeafChapters.length,
      onNavigate,
    });

  const isChapterRead =
    readingPosition != null && chapter.start_position != null
      ? readingPosition.index >= chapter.start_position.index
      : false;

  const prereading = prereadingByChapterId[chapter.id];

  const title = (
    <Typography
      variant="h6"
      component="span"
      sx={{
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        maxWidth: { xs: 'calc(100vw - 120px)', sm: 'calc(100vw - 200px)', md: '600px' },
        display: 'block',
      }}
    >
      {chapter.name}
    </Typography>
  );

  const renderContent = () => (
    <Box>
      <PrereadingSection
        chapterId={chapter.id}
        bookId={bookId}
        prereading={prereading}
        defaultExpanded={!isChapterRead}
      />
      <HighlightsSection
        chapter={chapter}
        bookId={bookId}
        bookmarksByHighlightId={bookmarksByHighlightId}
        availableTags={availableTags}
      />
      <FlashcardsSection chapter={chapter} bookId={bookId} />
    </Box>
  );

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      title={title}
      headerElement={
        hasNavigation ? (
          <ProgressBar currentIndex={currentIndex} totalCount={allLeafChapters.length} />
        ) : undefined
      }
      footerActions={
        <Box sx={{ display: 'flex', justifyContent: 'end', width: '100%' }}>
          <Button onClick={onClose}>Close</Button>
        </Box>
      }
    >
      {/* Desktop Layout: Navigation buttons on sides */}
      <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'flex-start', gap: 2 }}>
        {hasNavigation && (
          <IconButton
            onClick={handlePrevious}
            disabled={!hasPrevious}
            sx={{ flexShrink: 0, visibility: hasPrevious ? 'visible' : 'hidden', mt: 1 }}
            aria-label="Previous chapter"
          >
            <ArrowBackIcon />
          </IconButton>
        )}

        <Box display="flex" flexDirection="column" gap={3} flex={1} {...swipeHandlers}>
          <FadeInOut ekey={chapter.id}>{renderContent()}</FadeInOut>
        </Box>

        {hasNavigation && (
          <IconButton
            onClick={handleNext}
            disabled={!hasNext}
            sx={{ flexShrink: 0, visibility: hasNext ? 'visible' : 'hidden', mt: 1 }}
            aria-label="Next chapter"
          >
            <ArrowForwardIcon />
          </IconButton>
        )}
      </Box>

      {/* Mobile Layout: Navigation buttons below */}
      <Box
        sx={{ display: { xs: 'flex', sm: 'none' }, flexDirection: 'column', gap: 3 }}
        {...swipeHandlers}
      >
        <FadeInOut ekey={chapter.id}>{renderContent()}</FadeInOut>

        {hasNavigation && (
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, pt: 1 }}>
            <Button
              onClick={handlePrevious}
              disabled={!hasPrevious}
              startIcon={<ArrowBackIcon />}
              variant="outlined"
              sx={{ flex: 1, maxWidth: '200px' }}
            >
              Previous
            </Button>
            <Button
              onClick={handleNext}
              disabled={!hasNext}
              endIcon={<ArrowForwardIcon />}
              variant="outlined"
              sx={{ flex: 1, maxWidth: '200px' }}
            >
              Next
            </Button>
          </Box>
        )}
      </Box>
    </CommonDialog>
  );
};
