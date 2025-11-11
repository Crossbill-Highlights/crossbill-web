import { HighlightSearchResult } from '@/api/generated/model';
import { SectionTitle } from '@/components/common/SectionTitle';
import { Box, Typography } from '@mui/material';
import { chain, sortBy } from 'lodash';
import { HighlightCard } from './HighlightCard';

interface SearchResultsProps {
  isSearching: boolean;
  highlights: HighlightSearchResult[] | undefined;
  searchText: string;
  bookId: number;
}

export const SearchResults = ({
  isSearching,
  highlights,
  searchText,
  bookId,
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

  // Results display
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {highlights && highlights.length > 0 ? (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Found {highlights.length} highlight
            {highlights.length !== 1 ? 's' : ''}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {sortedChapters?.map((chapter) => (
              <Box key={chapter.chapterId ?? 'unknown'}>
                {/* Chapter Header */}
                <SectionTitle showDivider>{chapter.chapterName}</SectionTitle>

                {/* Highlights in this chapter */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {chapter.highlights.map((highlight) => (
                    <HighlightCard key={highlight.id} highlight={highlight} bookId={bookId} />
                  ))}
                </Box>
              </Box>
            ))}
          </Box>
        </>
      ) : (
        <Typography variant="body1" color="text.secondary">
          No highlights found matching "{searchText}"
        </Typography>
      )}
    </Box>
  );
};
