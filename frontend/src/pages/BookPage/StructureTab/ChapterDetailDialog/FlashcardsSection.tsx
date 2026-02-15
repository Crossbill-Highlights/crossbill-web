import type { ChapterWithHighlights } from '@/api/generated/model';
import type { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { FlashcardEditDialog } from '@/pages/BookPage/FlashcardsTab/FlashcardEditDialog.tsx';
import { FlashcardListCard } from '@/pages/BookPage/FlashcardsTab/FlashcardListCard.tsx';
import { Stack } from '@mui/material';
import { flatMap } from 'lodash';
import { useCallback, useMemo, useState } from 'react';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface FlashcardsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
}

export const FlashcardsSection = ({ chapter, bookId }: FlashcardsSectionProps) => {
  const [editingFlashcard, setEditingFlashcard] = useState<FlashcardWithContext | null>(null);

  const flashcardsWithContext = useMemo(
    (): FlashcardWithContext[] =>
      flatMap(chapter.highlights, (highlight) =>
        highlight.flashcards.map((flashcard) => ({
          ...flashcard,
          highlight,
          chapterName: chapter.name,
          chapterId: chapter.id,
          highlightTags: highlight.highlight_tags,
        }))
      ),
    [chapter]
  );

  const count = flashcardsWithContext.length;

  const handleEditFlashcard = useCallback((flashcard: FlashcardWithContext) => {
    setEditingFlashcard(flashcard);
  }, []);

  const handleCloseEdit = useCallback(() => {
    setEditingFlashcard(null);
  }, []);

  return (
    <>
      <CollapsibleSection title="Flashcards" count={count} defaultExpanded={count > 0}>
        <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
          {flashcardsWithContext.map((flashcard) => (
            <li key={flashcard.id}>
              <FlashcardListCard
                flashcard={flashcard}
                bookId={bookId}
                onEdit={() => handleEditFlashcard(flashcard)}
                showSourceHighlight={false}
              />
            </li>
          ))}
        </Stack>
      </CollapsibleSection>

      {editingFlashcard && (
        <FlashcardEditDialog
          flashcard={editingFlashcard}
          bookId={bookId}
          open={true}
          onClose={handleCloseEdit}
        />
      )}
    </>
  );
};
