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
import { ProgressBar } from '@/pages/BookPage/Highlights/HighlightViewModal/components/ProgressBar.tsx';
import { Box, Button, Tab, Tabs } from '@mui/material';
import { sumBy } from 'lodash';
import { useMemo, useState } from 'react';
import { AfterReadingSection } from './AfterReadingSection.tsx';
import { FlashcardsSection } from './FlashcardsSection.tsx';
import { HighlightsSection } from './HighlightsSection.tsx';
import { PrereadingQuestionsSection } from './PrereadingQuestionsSection.tsx';
import { PrereadingSummarySection } from './PrereadingSummarySection.tsx';
import { QuizChatDialog } from './QuizChatDialog.tsx';

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

const TAB_BEFORE_READING = 0;
const TAB_AFTER_READING = 1;
const TAB_HIGHLIGHTS = 2;
const TAB_FLASHCARDS = 3;

const formatTabLabel = (label: string, count: number) =>
  count > 0 ? `${label} (${count})` : label;

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
  const [quizOpen, setQuizOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(TAB_BEFORE_READING);

  const { hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext, swipeHandlers } =
    useModalHorizontalNavigation({
      open,
      currentIndex,
      totalCount: allLeafChapters.length,
      onNavigate,
    });

  const prereadingSummary = prereadingByChapterId[chapter.id];

  const highlightCount = chapter.highlights.length;
  const flashcardCount = useMemo(() => {
    const fromHighlights = sumBy(chapter.highlights, (h) => h.flashcards.length);
    const fromChapter = (bookFlashcards ?? []).filter((fc) => fc.chapter_id === chapter.id).length;
    return fromHighlights + fromChapter;
  }, [chapter, bookFlashcards]);

  const title = <CommonDialogTitle>{chapter.name}</CommonDialogTitle>;

  const renderContent = () => (
    <Box>
      <PrereadingSummarySection
        chapterId={chapter.id}
        bookId={bookId}
        prereadingSummary={prereadingSummary}
        defaultExpanded={true}
      />

      <Tabs
        value={activeTab}
        onChange={(_, newValue: number) => setActiveTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ borderBottom: 1, borderColor: 'divider', mt: 1 }}
        onTouchStart={(e) => e.stopPropagation()}
        onTouchMove={(e) => e.stopPropagation()}
        onTouchEnd={(e) => e.stopPropagation()}
      >
        <Tab label="Before reading" />
        <Tab label="After reading" />
        <Tab label={formatTabLabel('Highlights', highlightCount)} />
        <Tab label={formatTabLabel('Flashcards', flashcardCount)} />
      </Tabs>

      <Box sx={{ pt: 2, pb: 2 }}>
        {activeTab === TAB_BEFORE_READING && (
          <PrereadingQuestionsSection
            chapterId={chapter.id}
            bookId={bookId}
            prereadingSummary={prereadingSummary}
          />
        )}

        {activeTab === TAB_AFTER_READING && (
          <AfterReadingSection onStartQuiz={() => setQuizOpen(true)} />
        )}

        {activeTab === TAB_HIGHLIGHTS && (
          <HighlightsSection
            chapter={chapter}
            bookId={bookId}
            bookmarksByHighlightId={bookmarksByHighlightId}
            availableTags={availableTags}
          />
        )}

        {activeTab === TAB_FLASHCARDS && (
          <FlashcardsSection
            chapter={chapter}
            bookId={bookId}
            prereadingSummary={prereadingSummary}
            bookFlashcards={bookFlashcards}
          />
        )}
      </Box>
    </Box>
  );

  return (
    <>
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
      <QuizChatDialog
        open={quizOpen}
        onClose={() => setQuizOpen(false)}
        chapterId={chapter.id}
        chapterName={chapter.name}
      />
    </>
  );
};
