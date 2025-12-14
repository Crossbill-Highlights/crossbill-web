import type { Bookmark, Highlight } from '@/api/generated/model';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { SectionTitle } from '@/components/common/SectionTitle';
import { Box, Typography } from '@mui/material';
import { HighlightCard } from './HighlightCard';

export interface ChapterData {
  id: number | string;
  name: string;
  chapterNumber?: number;
  highlights: Highlight[];
}

interface ChapterListProps {
  chapters: ChapterData[];
  bookId: number;
  bookmarksByHighlightId: Record<number, Bookmark>;
  allHighlights: Highlight[];
  isLoading?: boolean;
  emptyMessage?: string;
  animationKey?: string;
}

export const ChapterList = ({
  chapters,
  bookId,
  bookmarksByHighlightId,
  allHighlights,
  isLoading,
  emptyMessage = 'No chapters found.',
  animationKey = 'chapters',
}: ChapterListProps) => {
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
            <Box key={chapter.id}>
              <SectionTitle showDivider>{chapter.name}</SectionTitle>

              {chapter.highlights.length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  {chapter.highlights.map((highlight) => {
                    const highlightIndex = allHighlights.findIndex((h) => h.id === highlight.id);
                    return (
                      <HighlightCard
                        key={highlight.id}
                        highlight={highlight}
                        bookId={bookId}
                        bookmark={bookmarksByHighlightId[highlight.id]}
                        bookmarksByHighlightId={bookmarksByHighlightId}
                        allHighlights={allHighlights}
                        currentIndex={highlightIndex}
                      />
                    );
                  })}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ pl: 0.5 }}>
                  No highlights found in this chapter.
                </Typography>
              )}
            </Box>
          ))
        )}
      </Box>
    </FadeInOut>
  );
};
