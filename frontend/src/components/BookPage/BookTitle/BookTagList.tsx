import { Box, Chip } from '@mui/material';

export const BookTagList: React.FC<{ tags?: { id: number; name: string }[] }> = ({ tags }) => {
  if (!tags || tags.length === 0) {
    return null;
  }
  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: { xs: 'center', lg: 'flex-start' },
        gap: 1,
        width: '100%',
      }}
    >
      {tags.map((tag) => (
        <Chip
          key={tag.id}
          label={tag.name}
          size="small"
          variant="outlined"
          sx={{ fontWeight: 500 }}
        />
      ))}
    </Box>
  );
};
