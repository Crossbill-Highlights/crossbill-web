import { Box, Chip } from '@mui/material';

export const BookTagList: React.FC<{ tags?: { id: number; name: string }[] }> = ({ tags }) => {
  if (!tags || tags.length === 0) {
    return null;
  }
  return (
    <Box
      component="ul"
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: { xs: 'center', lg: 'flex-start' },
        gap: 1,
        width: '100%',
        listStyle: 'none',
        p: 0,
        m: 0,
      }}
      aria-label="Tags"
    >
      {tags.map((tag) => (
        <Box component="li" key={tag.id}>
          <Chip label={tag.name} size="small" variant="outlined" sx={{ fontWeight: 500 }} />
        </Box>
      ))}
    </Box>
  );
};
