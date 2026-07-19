import { SearchBar } from '@/components/inputs/SearchBar.tsx';
import { SortIcon } from '@/theme/Icons.tsx';
import { Box, IconButton, Tooltip } from '@mui/material';

interface ListSearchSortHeaderProps {
  onSearch: (value: string) => void;
  searchPlaceholder: string;
  searchInitialValue: string;
  isReversed: boolean;
  onToggleReversed: () => void;
}

/**
 * Search field plus a newest/oldest sort toggle, as shown above the highlights
 * and flashcards lists. Identical across those tabs bar the search placeholder.
 */
export const ListSearchSortHeader = ({
  onSearch,
  searchPlaceholder,
  searchInitialValue,
  isReversed,
  onToggleReversed,
}: ListSearchSortHeaderProps) => (
  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
    <Box sx={{ flexGrow: 1 }}>
      <SearchBar
        onSearch={onSearch}
        placeholder={searchPlaceholder}
        initialValue={searchInitialValue}
      />
    </Box>
    <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
      <IconButton
        onClick={onToggleReversed}
        sx={{
          mt: '1px',
          color: isReversed ? 'primary.main' : 'text.secondary',
          '&:hover': { color: 'primary.main' },
        }}
      >
        <SortIcon />
      </IconButton>
    </Tooltip>
  </Box>
);
