import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useDeleteNoteApiV1NotesNoteIdDelete,
  useGetNoteApiV1NotesNoteIdGet,
} from '@/api/generated/notes/notes.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { CommonDialogTitle } from '@/components/dialogs/CommonDialogTitle.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { markdownStyles } from '@/theme/theme';
import { Box, Button, Chip, Stack, Typography, useTheme } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import { NoteEditorForm, type NoteEditorFormHandle } from './NoteEditorForm';
import { NoteToolbar } from './components/NoteToolbar';
import { NOTE_KIND_LABELS, type NoteKindValue } from './noteKinds';

interface NoteViewModalProps {
  /** Note to display; its full detail (with linked summaries) is fetched by id. */
  noteId: number;
  onClose: () => void;
}

/**
 * Read-only note detail dialog that toggles into an in-place editor. Read mode
 * shows the full note (content first) with an action toolbar underneath;
 * clicking Edit swaps the same dialog to the note editor form.
 *
 * Opened by note id (deep-linkable via the `noteId` URL param). Mounted only
 * while a note is open (keyed by id), mirroring the highlight modal — so
 * transient state resets naturally between notes.
 */
export const NoteViewModal = ({ noteId, onClose }: NoteViewModalProps) => {
  const theme = useTheme();
  const { book } = useBookPage();
  const { showSnackbar } = useSnackbar();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const formRef = useRef<NoteEditorFormHandle>(null);
  const [formStatus, setFormStatus] = useState({ isSaving: false, canSave: false });

  const { data: activeNote, isLoading, isError } = useGetNoteApiV1NotesNoteIdGet(noteId);

  const deleteMutation = useDeleteNoteApiV1NotesNoteIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(book.id),
        });
        setDeleteConfirmOpen(false);
        onClose();
      },
      onError: (error) => {
        console.error('Failed to delete note:', error);
        showSnackbar('Failed to delete note. Please try again.', 'error');
      },
    },
  });

  const handleCopy = async () => {
    if (!activeNote) return;
    await navigator.clipboard.writeText(activeNote.body);
    showSnackbar('Note copied to clipboard.', 'success');
  };

  const handleConfirmDelete = () => {
    void deleteMutation.mutateAsync({ noteId });
  };

  const isDeleting = deleteMutation.isPending;

  const chapters = activeNote?.chapters ?? [];
  const highlightTags = activeNote?.highlight_tags ?? [];
  const highlights = activeNote?.highlights ?? [];

  const footerActions = isEditing ? (
    <Box sx={{ display: 'flex', gap: 1, width: '100%', justifyContent: 'flex-end' }}>
      <Button onClick={() => setIsEditing(false)} disabled={formStatus.isSaving}>
        Cancel
      </Button>
      <Button
        variant="contained"
        onClick={() => formRef.current?.submit()}
        disabled={!formStatus.canSave}
      >
        {formStatus.isSaving ? 'Saving...' : 'Save'}
      </Button>
    </Box>
  ) : (
    <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
      <Button onClick={onClose} disabled={isDeleting}>
        Close
      </Button>
    </Box>
  );

  return (
    <CommonDialog
      open
      onClose={onClose}
      maxWidth="md"
      isLoading={isEditing ? formStatus.isSaving : isDeleting}
      title={
        <CommonDialogTitle>
          {isEditing ? 'Edit note' : (activeNote?.title ?? 'Note')}
        </CommonDialogTitle>
      }
      footerActions={footerActions}
    >
      <Box mt={2} mb={2}>
        {isEditing && activeNote ? (
          <NoteEditorForm
            ref={formRef}
            open={isEditing}
            note={activeNote}
            onSaved={() => setIsEditing(false)}
            onStatusChange={setFormStatus}
          />
        ) : activeNote ? (
          <Stack gap={2}>
            <Box>
              {activeNote.kind && (
                <Chip
                  size="small"
                  label={NOTE_KIND_LABELS[activeNote.kind as NoteKindValue]}
                  sx={{ mb: 1 }}
                />
              )}
              {activeNote.body && (
                <Box sx={markdownStyles(theme)}>
                  <ReactMarkdown>{activeNote.body}</ReactMarkdown>
                </Box>
              )}
              {(chapters.length > 0 || highlightTags.length > 0 || highlights.length > 0) && (
                <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: 'wrap', gap: 0.5 }}>
                  {chapters.map((chapter) => (
                    <Chip
                      key={`ch-${chapter.id}`}
                      size="small"
                      variant="outlined"
                      label={chapter.name}
                    />
                  ))}
                  {highlightTags.map((tag) => (
                    <Chip
                      key={`tag-${tag.id}`}
                      size="small"
                      variant="outlined"
                      label={`#${tag.name}`}
                    />
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
            <NoteToolbar
              onEdit={() => setIsEditing(true)}
              onCopy={() => void handleCopy()}
              onDelete={() => setDeleteConfirmOpen(true)}
              disabled={isDeleting}
            />
          </Stack>
        ) : isError ? (
          <Typography color="text.secondary">
            This note could not be found. It may have been deleted.
          </Typography>
        ) : (
          isLoading && <Spinner />
        )}
      </Box>

      <ConfirmationDialog
        open={deleteConfirmOpen}
        title="Delete note"
        message={`Delete note "${activeNote?.title ?? ''}"? This cannot be undone.`}
        confirmText="Delete"
        confirmColor="error"
        onConfirm={handleConfirmDelete}
        onClose={() => setDeleteConfirmOpen(false)}
        isLoading={isDeleting}
      />
    </CommonDialog>
  );
};
