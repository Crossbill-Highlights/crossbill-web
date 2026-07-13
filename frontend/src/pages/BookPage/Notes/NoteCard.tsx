import type { NoteWithLinks } from '@/api/generated/model';
import { Box, Chip, Stack, styled, Typography } from '@mui/material';

import { NOTE_KIND_LABELS, type NoteKindValue } from './noteKinds';

interface NoteCardProps {
  note: NoteWithLinks;
  onClick: () => void;
}

const NoteStyled = styled(Box)(({ theme }) => ({
  borderLeft: `3px solid ${theme.palette.primary.main}`,
  paddingLeft: theme.spacing(2),
  paddingTop: theme.spacing(2),
  paddingBottom: theme.spacing(2),
  cursor: 'pointer',
  transition: 'background-color 0.15s ease',
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
  '&:focus-visible': {
    outline: `2px solid ${theme.palette.primary.main}`,
    outlineOffset: 2,
  },
}));

export const NoteCard = ({ note, onClick }: NoteCardProps) => {
  const chapters = note.chapters ?? [];
  const highlightTags = note.highlight_tags ?? [];
  const highlights = note.highlights ?? [];

  return (
    <NoteStyled
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onClick();
        }
      }}
    >
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
        <Typography variant="h3">{note.title}</Typography>
        {note.kind && <Chip size="small" label={NOTE_KIND_LABELS[note.kind as NoteKindValue]} />}
      </Stack>
      {note.body && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {note.body}
        </Typography>
      )}
      {(chapters.length > 0 || highlightTags.length > 0 || highlights.length > 0) && (
        <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap', gap: 0.5 }}>
          {chapters.map((chapter) => (
            <Chip key={`ch-${chapter.id}`} size="small" variant="outlined" label={chapter.name} />
          ))}
          {highlightTags.map((tag) => (
            <Chip key={`tag-${tag.id}`} size="small" variant="outlined" label={`#${tag.name}`} />
          ))}
          {highlights.length > 0 && (
            <Chip
              size="small"
              variant="outlined"
              label={`${highlights.length} highlight${highlights.length === 1 ? '' : 's'}`}
            />
          )}
        </Stack>
      )}
    </NoteStyled>
  );
};
