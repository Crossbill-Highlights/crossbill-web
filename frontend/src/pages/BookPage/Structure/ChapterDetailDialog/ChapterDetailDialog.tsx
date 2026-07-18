import type {
  Bookmark,
  ChapterPrereadingResponse,
  ChapterWithHighlights,
  Flashcard,
  TagInBook,
} from '@/api/generated/model';
import { FadeInOut } from '@/components/animations/FadeInOut.tsx';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { CommonDialogHorizontalNavigation } from '@/components/dialogs/CommonDialogHorizontalNavigation.tsx';
import { CommonDialogTitle } from '@/components/dialogs/CommonDialogTitle.tsx';
import { DialogTabs, type DialogTabItem } from '@/components/dialogs/DialogTabs.tsx';
import { ProgressBar } from '@/components/dialogs/ProgressBar.tsx';
import {
  useModalHorizontalNavigation,
  useModalSwipeNavigation,
} from '@/components/dialogs/useModalHorizontalNavigation.ts';
import { NoteEditorDialog } from '@/pages/BookPage/Notes/NoteEditorDialog';
import { Box, Button } from '@mui/material';
import { sumBy } from 'lodash';
import { useMemo, useState } from 'react';
import { ChapterReviewSection } from './ChapterReviewSection.tsx';
import { ChapterToolbar } from './ChapterToolbar.tsx';
import { ChatDialog } from './ChatDialog.tsx';
import { CHAT_VARIANT, QUIZ_VARIANT } from './chatVariants.ts';
import { FlashcardsSection } from './FlashcardsSection.tsx';
import { HighlightsSection } from './HighlightsSection.tsx';
import { NotesSection } from './NotesSection.tsx';
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
  availableTags: TagInBook[];
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
  const [quizOpen, setQuizOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  // Lifted out of DialogTabs so the active tab survives chapter navigation
  // (the tab content remounts inside the chapter-keyed FadeInOut).
  const [activeTab, setActiveTab] = useState(0);
  const [chatNoteBody, setChatNoteBody] = useState<string | null>(null);

  const { hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext } =
    useModalHorizontalNavigation({
      open,
      currentIndex,
      totalCount: allLeafChapters.length,
      onNavigate,
    });

  const { swipeHandlers: summarySwipeHandlers } = useModalSwipeNavigation({
    currentIndex,
    totalCount: allLeafChapters.length,
    onNavigate,
  });

  const { swipeHandlers: tabSwipeHandlers } = useModalSwipeNavigation({
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

  const tabs: DialogTabItem[] = [
    {
      key: 'review',
      label: 'Chapter review',
      content: (
        <ChapterReviewSection
          chapterId={chapter.id}
          bookId={bookId}
          prereadingSummary={prereadingSummary}
          onStartQuiz={() => setQuizOpen(true)}
          onStartChat={() => setChatOpen(true)}
        />
      ),
    },
    {
      key: 'highlights',
      label: 'Highlights',
      count: highlightCount,
      content: (
        <HighlightsSection
          chapter={chapter}
          bookId={bookId}
          bookmarksByHighlightId={bookmarksByHighlightId}
          availableTags={availableTags}
        />
      ),
    },
    {
      key: 'flashcards',
      label: 'Flashcards',
      count: flashcardCount,
      content: (
        <FlashcardsSection
          chapter={chapter}
          bookId={bookId}
          prereadingSummary={prereadingSummary}
          bookFlashcards={bookFlashcards}
        />
      ),
    },
    {
      key: 'notes',
      label: 'Notes',
      content: <NotesSection chapter={chapter} bookId={bookId} />,
    },
  ];

  const renderContent = () => (
    <Box>
      <Box {...summarySwipeHandlers}>
        <PrereadingSummarySection prereadingSummary={prereadingSummary} defaultExpanded={true} />
      </Box>

      <ChapterToolbar chapterId={chapter.id} bookId={bookId} hasSummary={!!prereadingSummary} />

      <DialogTabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        panelSwipeHandlers={tabSwipeHandlers}
      />
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
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
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
        >
          <FadeInOut ekey={chapter.id}>{renderContent()}</FadeInOut>
        </CommonDialogHorizontalNavigation>
      </CommonDialog>
      <ChatDialog
        open={quizOpen}
        onClose={() => setQuizOpen(false)}
        chapterId={chapter.id}
        chapterName={chapter.name}
        variant={QUIZ_VARIANT}
      />
      <ChatDialog
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        chapterId={chapter.id}
        chapterName={chapter.name}
        variant={CHAT_VARIANT}
        onSaveNote={(content) => setChatNoteBody(content)}
      />
      <NoteEditorDialog
        open={chatNoteBody !== null}
        onClose={() => setChatNoteBody(null)}
        initialBody={chatNoteBody ?? ''}
        initialChapterIds={[chapter.id]}
      />
    </>
  );
};
