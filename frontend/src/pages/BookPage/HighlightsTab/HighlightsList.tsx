import type { Bookmark, Highlight } from '@/api/generated/model';
import { FadeInOut } from '@/components/animations/FadeInOut.tsx';
import { SectionTitle } from '@/components/typography/SectionTitle.tsx';
import { Box, Typography } from '@mui/material';
import { HighlightCard } from './HighlightCard.tsx';

export interface ChapterData {
  id: number;
  name: string;
  chapterNumber?: number;
  highlights: Highlight[];
}

interface ChapterListProps {
  chapters: ChapterData[];
  bookmarksByHighlightId: Record<number, Bookmark>;
  isLoading?: boolean;
  emptyMessage?: string;
  animationKey?: string;
  onOpenHighlight?: (highlightId: number) => void;
}

export const HighlightsList = ({
  chapters,
  bookmarksByHighlightId,
  isLoading,
  emptyMessage = 'No chapters found.',
  animationKey = 'chapters',
  onOpenHighlight,
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
            <Box key={chapter.id} id={`chapter-${chapter.id}`}>
              <SectionTitle showDivider>{chapter.name}</SectionTitle>

              {chapter.highlights.length > 0 ? (
                <Box
                  component="ul"
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2.5,
                    listStyle: 'none',
                    p: 0,
                    m: 0,
                  }}
                  aria-label={`Highlights in ${chapter.name}`}
                >
                  {chapter.highlights.map((highlight) => (
                    <li key={highlight.id}>
                      <HighlightCard
                        highlight={highlight}
                        bookmark={bookmarksByHighlightId[highlight.id]}
                        onOpenModal={onOpenHighlight}
                      />
                    </li>
                  ))}
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
