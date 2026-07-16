import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  getSearchBookHighlightsApiV1BooksBookIdHighlightsGetQueryKey,
  useUpdateHighlightNoteApiV1HighlightsHighlightIdNotePost,
} from '@/api/generated/highlights/highlights.ts';
import type {
  BookDetails,
  BookHighlightSearchResponse,
  ChapterWithHighlights,
} from '@/api/generated/model';
import { Collapsable } from '@/components/animations/Collapsable.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { Box, Button, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface HighlightNoteProps {
  highlightId: number;
  bookId: number;
  initialNote: string | null | undefined;
  visible: boolean;
  disabled?: boolean;
}

export const HighlightNote = ({
  highlightId,
  bookId,
  initialNote,
  visible,
  disabled = false,
}: HighlightNoteProps) => {
  const [noteText, setNoteText] = useState<string>(initialNote || '');
  const { showSnackbar } = useSnackbar();
  const { isProcessing, saveNote } = useNoteMutations(bookId, highlightId, showSnackbar);
  const hasChanges = (noteText.trim() || null) !== (initialNote || null);
  const isDisabled = disabled || isProcessing;

  return (
    <Collapsable isExpanded={visible}>
      <Box>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Note
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, alignItems: 'flex-start' }}>
          <TextField
            fullWidth
            multiline
            minRows={2}
            maxRows={6}
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Add a note about this highlight..."
            disabled={isDisabled}
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
            <Button
              variant="text"
              size={'small'}
              onClick={() => saveNote(noteText)}
              disabled={isDisabled || !hasChanges}
              sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
            >
              {isProcessing ? 'Saving...' : 'Save'}
            </Button>
          </Box>
        </Box>
      </Box>
    </Collapsable>
  );
};

/**
 * Return a copy of `chapters` with the note of the given highlight replaced.
 * The chapter/highlight objects are only cloned along the affected path so
 * downstream memoized selectors recompute for the changed highlight.
 */
const withPatchedHighlightNote = (
  chapters: ChapterWithHighlights[],
  highlightId: number,
  note: string | null
): ChapterWithHighlights[] =>
  chapters.map((chapter) =>
    chapter.highlights.some((highlight) => highlight.id === highlightId)
      ? {
          ...chapter,
          highlights: chapter.highlights.map((highlight) =>
            highlight.id === highlightId ? { ...highlight, note } : highlight
          ),
        }
      : chapter
  );

const useNoteMutations = (
  bookId: number,
  highlightId: number,
  showSnackbar: (message: string, severity: 'error' | 'warning' | 'info' | 'success') => void
) => {
  const queryClient = useQueryClient();
  const [isProcessing, setIsProcessing] = useState(false);

  const updateNoteMutation = useUpdateHighlightNoteApiV1HighlightsHighlightIdNotePost({
    mutation: {
      onSuccess: (response) => {
        const note = response.highlight.note ?? null;

        // Update the cached highlight in place so the new note shows immediately
        // in every view (highlight cards, the modal's highlight data) without
        // waiting for a refetch. The modal can be driven either by the book
        // details query or by the search query, so patch both.
        queryClient.setQueryData<BookDetails>(
          getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
          (old) =>
            old
              ? { ...old, chapters: withPatchedHighlightNote(old.chapters, highlightId, note) }
              : old
        );
        queryClient.setQueriesData<BookHighlightSearchResponse>(
          { queryKey: getSearchBookHighlightsApiV1BooksBookIdHighlightsGetQueryKey(bookId) },
          (old) =>
            old
              ? { ...old, chapters: withPatchedHighlightNote(old.chapters, highlightId, note) }
              : old
        );

        // Keep the server as the source of truth for anything the in-place
        // patch didn't cover.
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to update note:', error);
        showSnackbar('Failed to update note. Please try again.', 'error');
      },
    },
  });

  const saveNote = async (noteText: string) => {
    setIsProcessing(true);
    try {
      await updateNoteMutation.mutateAsync({
        highlightId,
        data: { note: noteText.trim() || null },
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    isProcessing,
    saveNote,
  };
};
