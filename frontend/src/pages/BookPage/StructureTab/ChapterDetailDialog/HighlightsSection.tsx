import type { Bookmark, ChapterWithHighlights, HighlightTagInBook } from '@/api/generated/model';
import { HighlightCard } from '@/pages/BookPage/HighlightsTab/HighlightCard.tsx';
import { HighlightViewModal } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx';
import { Stack } from '@mui/material';
import { useCallback, useMemo, useState } from 'react';
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
  const [selectedHighlightIndex, setSelectedHighlightIndex] = useState<number | null>(null);

  const highlights = chapter.highlights;
  const count = highlights.length;

  const selectedHighlight = useMemo(
    () => (selectedHighlightIndex !== null ? (highlights[selectedHighlightIndex] ?? null) : null),
    [highlights, selectedHighlightIndex]
  );

  const handleOpenHighlight = useCallback(
    (highlightId: number) => {
      const index = highlights.findIndex((h) => h.id === highlightId);
      if (index !== -1) setSelectedHighlightIndex(index);
    },
    [highlights]
  );

  const handleCloseHighlight = useCallback(() => {
    setSelectedHighlightIndex(null);
  }, []);

  const handleNavigateHighlight = useCallback((newIndex: number) => {
    setSelectedHighlightIndex(newIndex);
  }, []);

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

      {selectedHighlight && (
        <HighlightViewModal
          highlight={selectedHighlight}
          bookId={bookId}
          open={true}
          onClose={handleCloseHighlight}
          availableTags={availableTags}
          bookmarksByHighlightId={bookmarksByHighlightId}
          allHighlights={highlights}
          currentIndex={selectedHighlightIndex ?? 0}
          onNavigate={handleNavigateHighlight}
        />
      )}
    </>
  );
};
