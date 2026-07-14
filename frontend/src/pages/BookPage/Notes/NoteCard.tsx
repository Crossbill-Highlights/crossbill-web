import type { NoteWithLinks } from '@/api/generated/model';
import { markdownStyles } from '@/theme/theme';
import { Box, Chip, Stack, styled, Typography, useTheme } from '@mui/material';
import ReactMarkdown from 'react-markdown';

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
  const theme = useTheme();

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
        <Box
          sx={{
            ...markdownStyles(theme),
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          <ReactMarkdown>{note.body}</ReactMarkdown>
        </Box>
      )}
    </NoteStyled>
  );
};
