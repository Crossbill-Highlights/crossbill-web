import type { Bookmark, ChapterWithHighlights, HighlightTagInBook } from '@/api/generated/model';
import { HighlightCard } from '@/pages/BookPage/HighlightsTab/HighlightCard.tsx';
import { HighlightViewModal } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx';
import { useHighlightModal } from '@/pages/BookPage/HighlightsTab/hooks/useHighlightModal.ts';
import { Stack } from '@mui/material';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface HighlightsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
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
  const count = highlights.length;

  const {
    currentHighlight,
    currentHighlightIndex,
    handleOpenHighlight,
    handleCloseHighlight,
    handleModalNavigate,
  } = useHighlightModal({ allHighlights: highlights, isMobile: false, syncToUrl: false });

  return (
    <>
      <CollapsibleSection title="Highlights" count={count} defaultExpanded={count > 0}>
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
      </CollapsibleSection>

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
