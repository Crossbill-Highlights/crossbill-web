import { Box, TextField } from '@mui/material';

interface SearchBarProps {
  searchInput: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onClear: () => void;
}

export const SearchBar = ({ searchInput, onChange, onClear }: SearchBarProps) => {
  return (
    <Box sx={{ mb: 3 }}>
      <TextField
        fullWidth
        placeholder="Search highlights..."
        value={searchInput}
        onChange={onChange}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            onClear();
          }
        }}
        slotProps={{
          input: {
            endAdornment: searchInput && (
              <Box
                component="span"
                onClick={onClear}
                sx={{
                  cursor: 'pointer',
                  color: 'text.secondary',
                  '&:hover': { color: 'text.primary' },
                }}
              >
                ✕
              </Box>
            ),
          },
        }}
        sx={{
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: 'divider',
            },
          },
        }}
      />
    </Box>
  );
};
