import { Box, Typography } from '@mui/material';
import { Highlight } from '@/api/generated/model';
import { HighlightCard } from './HighlightCard';

interface SearchResultsProps {
  isSearching: boolean;
  highlights: Highlight[] | undefined;
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

  // Results display
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {highlights && highlights.length > 0 ? (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Found {highlights.length} highlight
            {highlights.length !== 1 ? 's' : ''}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {highlights.map((highlight) => (
              <HighlightCard key={highlight.id} highlight={highlight} bookId={bookId} />
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
