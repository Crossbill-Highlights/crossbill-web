import type { Flashcard, Highlight } from '@/api/generated/model';
import { FlashcardListCard } from '@/components/BookPage/FlashcardsTab/FlashcardListCard.tsx';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { SectionTitle } from '@/components/common/SectionTitle.tsx';
import { Box, Typography } from '@mui/material';

export interface FlashcardWithContext extends Flashcard {
  highlight: Highlight;
  chapterName: string;
  chapterId: number;
  highlightTags: { id: number; name: string }[];
}

export interface FlashcardChapterData {
  id: number;
  name: string;
  flashcards: FlashcardWithContext[];
  chapter_number?: number;
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
}: FlashcardChapterListProps) => {
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Searching...
        </Typography>
      </Box>
    );
  }

  return (
    <FadeInOut ekey={animationKey}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {chapters.length === 0 ? (
          <Typography variant="body1" color="text.secondary">
            {emptyMessage}
          </Typography>
        ) : (
          chapters.map((chapter) => (
            <Box key={chapter.id} id={`chapter-${chapter.id}`}>
              <SectionTitle showDivider>{chapter.name}</SectionTitle>

              <Box
                component="ul"
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(2, 1fr)',
                  },
                  gap: 2,
                  listStyle: 'none',
                  p: 0,
                  m: 0,
                }}
                aria-label={`Flashcards in ${chapter.name}`}
              >
                {chapter.flashcards.map((flashcard) => (
                  <FlashcardListCard
                    key={flashcard.id}
                    flashcard={flashcard}
                    bookId={bookId}
                    onEdit={() => onEditFlashcard(flashcard)}
                  />
                ))}
              </Box>
            </Box>
          ))
        )}
      </Box>
    </FadeInOut>
  );
};
