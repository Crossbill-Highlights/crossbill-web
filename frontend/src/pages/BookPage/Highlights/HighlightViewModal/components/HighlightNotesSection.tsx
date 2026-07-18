import type { Highlight, NoteWithLinks } from '@/api/generated/model';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { NoteCard } from '@/pages/BookPage/Notes/NoteCard';
import { NoteModals } from '@/pages/BookPage/Notes/NoteModals';
import { NotePickerDialog } from '@/pages/BookPage/Notes/components/NotePickerDialog.tsx';
import { useNoteLinks } from '@/pages/BookPage/Notes/hooks/useNoteLinks';
import { useNoteModals } from '@/pages/BookPage/Notes/hooks/useNoteModals';
import { AddIcon, LinkIcon, LinkOffIcon } from '@/theme/Icons.tsx';
import { Box, Button, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { useState } from 'react';

interface HighlightNotesSectionProps {
  highlight: Highlight;
  bookId: number;
  /** Notes linked to the highlight; the query lives in HighlightTabs for the tab count. */
  notes: NoteWithLinks[];
  isLoading: boolean;
  disabled?: boolean;
}

/**
 * Notes tab of the highlight modal: lists notes linked to the highlight and
 * offers creating a new pre-linked note, linking an existing one, or removing
 * a link. Link changes invalidate the notes-for-book query (prefix match), so
 * the filtered list here refreshes immediately.
 */
export const HighlightNotesSection = ({
  highlight,
  bookId,
  notes,
  isLoading,
  disabled = false,
}: HighlightNotesSectionProps) => {
  const noteModals = useNoteModals({ syncToUrl: false });
  const [pickerOpen, setPickerOpen] = useState(false);
  const noteLinks = useNoteLinks({ bookId });

  const isDisabled = disabled || noteLinks.isPending;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={<LinkIcon />}
          onClick={() => setPickerOpen(true)}
          disabled={isDisabled}
        >
          Link existing note
        </Button>
        <Button
          variant="outlined"
          size="small"
          startIcon={<AddIcon />}
          onClick={noteModals.openCreate}
          disabled={isDisabled}
        >
          Add note
        </Button>
      </Box>
      {isLoading && <Spinner />}
      {!isLoading && notes.length === 0 && (
        <Typography color="text.secondary">No notes linked to this highlight.</Typography>
      )}
      <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
        {notes.map((note) => (
          <li key={note.id}>
            <NoteCard
              note={note}
              onClick={() => noteModals.openView(note)}
              action={
                <Tooltip title="Unlink from highlight">
                  <IconButton
                    aria-label="Unlink note"
                    size="small"
                    disabled={isDisabled}
                    onClick={(event) => {
                      event.stopPropagation();
                      noteLinks.unlinkHighlight(note, highlight.id);
                    }}
                  >
                    <LinkOffIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              }
            />
          </li>
        ))}
      </Stack>
      <NoteModals
        controller={noteModals}
        initialChapterIds={highlight.chapter_id ? [highlight.chapter_id] : []}
        initialHighlightIds={[highlight.id]}
      />
      <NotePickerDialog
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        bookId={bookId}
        title="Add highlight to note"
        onSelect={(note) =>
          noteLinks.linkHighlight(note, highlight.id, { onSuccess: () => setPickerOpen(false) })
        }
      />
    </Box>
  );
};
