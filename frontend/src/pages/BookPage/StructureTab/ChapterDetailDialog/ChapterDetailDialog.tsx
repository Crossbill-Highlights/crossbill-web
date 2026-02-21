import type {
  Bookmark,
  ChapterPrereadingResponse,
  ChapterWithHighlights,
  Flashcard,
  HighlightTagInBook,
} from '@/api/generated/model';
import { FadeInOut } from '@/components/animations/FadeInOut.tsx';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { CommonDialogHorizontalNavigation } from '@/components/dialogs/CommonDialogHorizontalNavigation.tsx';
import { CommonDialogTitle } from '@/components/dialogs/CommonDialogTitle.tsx';
import { useModalHorizontalNavigation } from '@/components/dialogs/useModalHorizontalNavigation.ts';
import { ProgressBar } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/components/ProgressBar.tsx';
import { Box, Button } from '@mui/material';
import { FlashcardsSection } from './FlashcardsSection.tsx';
import { HighlightsSection } from './HighlightsSection.tsx';
import { PrereadingSummarySection } from './PrereadingSummarySection.tsx';

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
  bookFlashcards?: Flashcard[];
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
  bookFlashcards,
}: ChapterDetailDialogProps) => {
  const { hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext, swipeHandlers } =
    useModalHorizontalNavigation({
      open,
      currentIndex,
      totalCount: allLeafChapters.length,
      onNavigate,
    });

  const prereadingSummary = prereadingByChapterId[chapter.id];

  const title = <CommonDialogTitle>{chapter.name}</CommonDialogTitle>;

  const renderContent = () => (
    <Box>
      <PrereadingSummarySection
        chapterId={chapter.id}
        bookId={bookId}
        prereadingSummary={prereadingSummary}
        defaultExpanded={true}
      />
      <HighlightsSection
        chapter={chapter}
        bookId={bookId}
        bookmarksByHighlightId={bookmarksByHighlightId}
        availableTags={availableTags}
      />
      <FlashcardsSection
        chapter={chapter}
        bookId={bookId}
        prereadingSummary={prereadingSummary}
        bookFlashcards={bookFlashcards}
      />
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
      <CommonDialogHorizontalNavigation
        hasNavigation={hasNavigation}
        hasPrevious={hasPrevious}
        hasNext={hasNext}
        onPrevious={handlePrevious}
        onNext={handleNext}
        swipeHandlers={swipeHandlers}
      >
        <FadeInOut ekey={chapter.id}>{renderContent()}</FadeInOut>
      </CommonDialogHorizontalNavigation>
    </CommonDialog>
  );
};
