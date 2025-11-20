import { Bookmark, HighlightSearchResult } from '@/api/generated/model';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { SectionTitle } from '@/components/common/SectionTitle';
import { Box, Typography } from '@mui/material';
import { chain, sortBy } from 'lodash';
import { AnimatePresence } from 'motion/react';
import { HighlightCard } from './HighlightCard';

interface SearchResultsProps {
  isSearching: boolean;
  highlights: HighlightSearchResult[] | undefined;
  searchText: string;
  bookId: number;
  bookmarksByHighlightId?: Record<number, Bookmark>;
  selectedTagId?: number | null;
}

export const SearchResults = ({
  isSearching,
  highlights,
  searchText,
  bookId,
  bookmarksByHighlightId = {},
  selectedTagId,
}: SearchResultsProps) => {
  // Loading state
  if (isSearching) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Searching...
        </Typography>
      </Box>
    );
  }

  // Group highlights by chapter and sort chapters by chapter_number
  const sortedChapters = chain(highlights)
    .groupBy((highlight) => highlight.chapter_id ?? 'null')
    .map((chapterHighlights, chapterIdStr) => ({
      chapterId: chapterIdStr === 'null' ? null : Number(chapterIdStr),
      chapterName: chapterHighlights[0]?.chapter_name ?? 'Unknown Chapter',
      chapterNumber: chapterHighlights[0]?.chapter_number,
      highlights: sortBy(chapterHighlights, (highlight) => highlight.page ?? Infinity),
    }))
    .sortBy((chapter) => {
      // Sort by chapter_number if available, otherwise by chapter_id
      // Chapters without number go to the end
      if (chapter.chapterNumber !== null && chapter.chapterNumber !== undefined) {
        return chapter.chapterNumber;
      }
      return (chapter.chapterId ?? 0) + 1000000; // Large offset to put them at the end
    })
    .value();

  // Create a flat array of all highlights for navigation
  const allHighlights = highlights || [];

  // Results display
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {highlights && highlights.length > 0 ? (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Found {highlights.length} highlight
            {highlights.length !== 1 ? 's' : ''}
          </Typography>
          <AnimatePresence>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {sortedChapters?.map((chapter) => {
                const key = chapter.chapterId ?? 'unknown';
                return (
                  <FadeInOut key={key} ekey={key}>
                    <Box>
                      {/* Chapter Header */}
                      <SectionTitle showDivider>{chapter.chapterName}</SectionTitle>

                      {/* Highlights in this chapter */}
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                        {chapter.highlights.map((highlight) => {
                          const highlightIndex = allHighlights.findIndex(
                            (h) => h.id === highlight.id
                          );
                          return (
                            <HighlightCard
                              key={highlight.id}
                              highlight={highlight}
                              bookId={bookId}
                              bookmark={bookmarksByHighlightId[highlight.id]}
                              allHighlights={allHighlights}
                              currentIndex={highlightIndex}
                            />
                          );
                        })}
                      </Box>
                    </Box>
                  </FadeInOut>
                );
              })}
            </Box>
          </AnimatePresence>
        </>
      ) : (
        <Typography variant="body1" color="text.secondary">
          {selectedTagId
            ? `No highlights found matching "${searchText}" with the selected tag`
            : `No highlights found matching "${searchText}"`}
        </Typography>
      )}
    </Box>
  );
};
