import type { Bookmark, ChapterWithHighlights, HighlightTagInBook } from '@/api/generated/model';
import { HighlightCard } from '@/pages/BookPage/Highlights/HighlightCard.tsx';
import { HighlightViewModal } from '@/pages/BookPage/Highlights/HighlightViewModal/HighlightViewModal.tsx';
import { useHighlightModal } from '@/pages/BookPage/Highlights/hooks/useHighlightModal.ts';
import { Stack, Typography } from '@mui/material';

interface HighlightsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: string;
  bookmarksByHighlightId: Record<number, Bookmark>;
  availableTags: HighlightTagInBook[];
}

export const HighlightsSection = ({
  chapter,
  bookId,
  bookmarksByHighlightId,
  availableTags,
}: HighlightsSectionProps) => {
  const highlights = chapter.highlights;

  const {
    currentHighlight,
    currentHighlightIndex,
    handleOpenHighlight,
    handleCloseHighlight,
    handleModalNavigate,
  } = useHighlightModal({ allHighlights: highlights, isMobile: false, syncToUrl: false });

  if (highlights.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No highlights in this chapter yet.
      </Typography>
    );
  }

  return (
    <>
      <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
        {highlights.map((highlight) => (
          <li key={highlight.id}>
            <HighlightCard
              highlight={highlight}
              bookmark={bookmarksByHighlightId[highlight.id]}
              onOpenModal={handleOpenHighlight}
            />
          </li>
        ))}
      </Stack>

      {currentHighlight && (
        <HighlightViewModal
          highlight={currentHighlight}
          bookId={bookId}
          open={true}
          onClose={handleCloseHighlight}
          availableTags={availableTags}
          bookmarksByHighlightId={bookmarksByHighlightId}
          allHighlights={highlights}
          currentIndex={currentHighlightIndex}
          onNavigate={handleModalNavigate}
        />
      )}
    </>
  );
};
