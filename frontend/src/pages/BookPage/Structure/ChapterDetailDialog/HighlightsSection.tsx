import type { Bookmark, ChapterWithHighlights, TagInBook } from '@/api/generated/model';
import { CardList } from '@/components/CardList.tsx';
import { EmptyStateText } from '@/components/EmptyStateText.tsx';
import { HighlightCard } from '@/components/cards/HighlightCard.tsx';
import { HighlightViewModal } from '@/pages/BookPage/Highlights/HighlightViewModal/HighlightViewModal.tsx';
import { useHighlightModal } from '@/pages/BookPage/Highlights/hooks/useHighlightModal.ts';

interface HighlightsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
  bookmarksByHighlightId: Record<number, Bookmark>;
  availableTags: TagInBook[];
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
    return <EmptyStateText>No highlights in this chapter yet.</EmptyStateText>;
  }

  return (
    <>
      <CardList>
        {highlights.map((highlight) => (
          <li key={highlight.id}>
            <HighlightCard
              highlight={highlight}
              bookmark={bookmarksByHighlightId[highlight.id]}
              onOpenModal={handleOpenHighlight}
            />
          </li>
        ))}
      </CardList>

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
