import type { Highlight } from '@/api/generated/model';
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
import { useNavigate } from '@tanstack/react-router';
import { useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import { NoteEditorForm, type NoteEditorFormHandle } from './NoteEditorForm';
import { NoteLinkTabs } from './components/NoteLinkTabs';
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
  const navigate = useNavigate();

  // Navigating to another route drops the `noteId` param, so the note modal
  // closes naturally as the target entity's deep link opens its modal there.
  const handleOpenHighlight = (highlightId: number) => {
    void navigate({
      to: '/book/$bookId/highlights',
      params: { bookId: String(book.id) },
      search: { highlightId },
    });
  };

  const handleOpenChapter = (chapterId: number) => {
    void navigate({
      to: '/book/$bookId/structure',
      params: { bookId: String(book.id) },
      search: { chapterId },
    });
  };

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
  const tags = activeNote?.tags ?? [];
  // The note detail returns lightweight highlight summaries; resolve them to the
  // full Highlight objects already loaded on the book so we can render HighlightCard.
  const highlights = useMemo<Highlight[]>(() => {
    if (!activeNote?.highlights?.length) return [];
    const byId = new Map<number, Highlight>();
    for (const chapter of book.chapters) {
      for (const highlight of chapter.highlights) {
        byId.set(highlight.id, highlight);
      }
    }
    return activeNote.highlights
      .map((summary) => byId.get(summary.id))
      .filter((highlight): highlight is Highlight => highlight !== undefined);
  }, [book.chapters, activeNote]);

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
          {activeNote?.kind && (
            <Chip
              size="small"
              label={NOTE_KIND_LABELS[activeNote.kind as NoteKindValue]}
              sx={{ mb: 0.5, ml: 1 }}
            />
          )}
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
              {activeNote.body && (
                <Box sx={markdownStyles(theme)}>
                  <ReactMarkdown>{activeNote.body}</ReactMarkdown>
                </Box>
              )}
              {tags.length > 0 && (
                <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: 'wrap', gap: 0.5 }}>
                  {tags.map((tag) => (
                    <Chip
                      key={`tag-${tag.id}`}
                      size="small"
                      variant="outlined"
                      label={`#${tag.name}`}
                    />
                  ))}
                </Stack>
              )}
            </Box>
            <NoteToolbar
              onEdit={() => setIsEditing(true)}
              onCopy={() => void handleCopy()}
              onDelete={() => setDeleteConfirmOpen(true)}
              disabled={isDeleting}
            />
            {(highlights.length > 0 || chapters.length > 0) && (
              <NoteLinkTabs
                highlights={highlights}
                chapters={chapters}
                onOpenHighlight={handleOpenHighlight}
                onOpenChapter={handleOpenChapter}
              />
            )}
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
