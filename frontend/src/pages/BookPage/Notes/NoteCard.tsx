import type { NoteWithLinks } from '@/api/generated/model';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { DeleteIcon, EditIcon } from '@/theme/Icons.tsx';
import { markdownStyles } from '@/theme/theme';
import { Box, Chip, Stack, styled, Typography, useTheme } from '@mui/material';
import ReactMarkdown from 'react-markdown';

import { NOTE_KIND_LABELS, type NoteKindValue } from './noteKinds';

interface NoteCardProps {
  note: NoteWithLinks;
  onEdit: () => void;
  onDelete: () => void;
}

const NoteStyled = styled(Box)(({ theme }) => ({
  position: 'relative',
  borderLeft: `3px solid ${theme.palette.primary.main}`,
  paddingLeft: theme.spacing(2),
  paddingTop: theme.spacing(1),
  paddingBottom: theme.spacing(1),
  transition: 'background-color 0.15s ease',
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
}));

const ActionButtonsStyled = styled(Box)(() => ({
  position: 'absolute',
  top: 8,
  right: 0,
  display: 'flex',
  gap: 0.5,
  zIndex: 1,
  opacity: 0.7,
  transition: 'opacity 0.2s ease',
  '&:hover': {
    opacity: 1,
  },
}));

export const NoteCard = ({ note, onEdit, onDelete }: NoteCardProps) => {
  const theme = useTheme();

  const chapters = note.chapters ?? [];
  const highlightTags = note.highlight_tags ?? [];
  const highlights = note.highlights ?? [];

  return (
    <NoteStyled>
      <Box sx={{ pr: 8 }}>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
          <Typography variant="h6">{note.title}</Typography>
          {note.kind && <Chip size="small" label={NOTE_KIND_LABELS[note.kind as NoteKindValue]} />}
        </Stack>
        {note.body && (
          <Box sx={markdownStyles(theme)}>
            <ReactMarkdown>{note.body}</ReactMarkdown>
          </Box>
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
      </Box>
      <ActionButtonsStyled>
        <IconButtonWithTooltip
          title="Edit note"
          ariaLabel="Edit note"
          onClick={onEdit}
          icon={<EditIcon />}
        />
        <IconButtonWithTooltip
          title="Delete note"
          ariaLabel="Delete note"
          onClick={onDelete}
          icon={<DeleteIcon />}
        />
      </ActionButtonsStyled>
    </NoteStyled>
  );
};
