import type { Flashcard, Highlight } from '@/api/generated/model';
import { FlashcardListCard } from '@/pages/BookPage/Flashcards/FlashcardListCard.tsx';
import { ChapterGroupedList } from '@/pages/BookPage/common/ChapterGroupedList.tsx';

export interface FlashcardWithContext extends Flashcard {
  highlight: Highlight | null;
  chapterName: string;
  chapterId: number | null;
  tags: { id: number; name: string }[];
}

export interface FlashcardChapterData {
  id: number;
  name: string;
  flashcards: FlashcardWithContext[];
}

interface FlashcardChapterListProps {
  chapters: FlashcardChapterData[];
  bookId: number;
  isLoading?: boolean;
  emptyMessage?: string;
  animationKey?: string;
  onEditFlashcard: (flashcard: FlashcardWithContext) => void;
}

export const FlashcardChapterList = ({
  chapters,
  bookId,
  isLoading,
  emptyMessage = 'No flashcards found.',
  animationKey = 'flashcard-chapters',
  onEditFlashcard,
}: FlashcardChapterListProps) => (
  <ChapterGroupedList
    chapters={chapters}
    getChapterId={(chapter) => chapter.id}
    getChapterName={(chapter) => chapter.name}
    getItems={(chapter) => chapter.flashcards}
    getItemKey={(flashcard) => flashcard.id}
    ariaLabel={(chapterName) => `Flashcards in ${chapterName}`}
    isLoading={isLoading}
    emptyMessage={emptyMessage}
    animationKey={animationKey}
    renderItem={(flashcard) => (
      <FlashcardListCard
        flashcard={flashcard}
        bookId={bookId}
        onEdit={() => onEditFlashcard(flashcard)}
      />
    )}
  />
);
