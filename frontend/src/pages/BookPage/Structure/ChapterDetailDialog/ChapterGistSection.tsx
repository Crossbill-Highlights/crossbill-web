import type { NoteWithLinks } from '@/api/generated/model';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { NoteEditorDialog } from '@/pages/BookPage/Notes/NoteEditorDialog';
import { EditIcon } from '@/theme/Icons.tsx';
import { Box, Button, Typography } from '@mui/material';
import { find } from 'lodash';
import { useState } from 'react';

interface ChapterGistSectionProps {
  chapterId: number;
  chapterName: string;
  notes: NoteWithLinks[];
}

export const ChapterGistSection = ({ chapterId, chapterName, notes }: ChapterGistSectionProps) => {
  const [editorOpen, setEditorOpen] = useState(false);

  const gist = find(notes, (note) => note.kind === 'gist') ?? null;

  return (
    <Box sx={{ mb: 2 }}>
      {gist ? (
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Your gist
            </Typography>
            <Typography variant="body1">{gist.body}</Typography>
          </Box>
          <IconButtonWithTooltip
            title="Edit gist"
            ariaLabel="Edit gist"
            icon={<EditIcon fontSize="small" />}
            onClick={() => setEditorOpen(true)}
          />
        </Box>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            What was this chapter about, in your words? Capturing it in a sentence or two is the
            best way to make it stick.
          </Typography>
          <Button variant="outlined" size="small" onClick={() => setEditorOpen(true)}>
            Write gist
          </Button>
        </Box>
      )}
      <NoteEditorDialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        note={gist}
        initialKind="gist"
        initialBody={gist ? undefined : ''}
        initialChapterIds={[chapterId]}
        initialTitle={chapterName}
      />
    </Box>
  );
};
