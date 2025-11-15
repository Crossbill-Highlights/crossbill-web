import { HighlightTagInBook } from '@/api/generated/model';
import { Close as CloseIcon, LocalOffer as TagIcon } from '@mui/icons-material';
import { Box, Chip, IconButton, Typography } from '@mui/material';

interface HighlightTagsProps {
  tags: HighlightTagInBook[];
  selectedTag?: number | null;
  onTagClick: (tagId: number | null) => void;
}

export const HighlightTags = ({ tags, selectedTag, onTagClick }: HighlightTagsProps) => {
  if (!tags || tags.length === 0) {
    return null;
  }

  // Sort tags alphabetically
  const sortedTags = [...tags].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <Box
      sx={{
        position: 'sticky',
        top: 24,
        p: 3,
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: 1,
        borderColor: 'divider',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TagIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
            Tags
          </Typography>
        </Box>
        {selectedTag && (
          <IconButton size="small" onClick={() => onTagClick(null)} title="Clear filter">
            <CloseIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {sortedTags.map((tag) => (
          <Chip
            key={tag.id}
            label={tag.name}
            size="small"
            variant={selectedTag === tag.id ? 'filled' : 'outlined'}
            color={selectedTag === tag.id ? 'primary' : 'default'}
            onClick={() => onTagClick(tag.id)}
            sx={{
              cursor: 'pointer',
              '&:hover': {
                bgcolor: selectedTag === tag.id ? 'primary.dark' : 'action.hover',
              },
            }}
          />
        ))}
      </Box>
    </Box>
  );
};
