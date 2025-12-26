import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useUpdateHighlightNoteApiV1HighlightsHighlightIdNotePost } from '@/api/generated/highlights/highlights.ts';
import { Collapsable } from '@/components/common/animations/Collapsable.tsx';
import { Box, Button, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

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
  const queryClient = useQueryClient();
  const [noteText, setNoteText] = useState<string>(initialNote || '');
  const [isSaving, setIsSaving] = useState(false);

  // Update note when initialNote changes
  useEffect(() => {
    setNoteText(initialNote || '');
  }, [initialNote]);

  const updateNoteMutation = useUpdateHighlightNoteApiV1HighlightsHighlightIdNotePost({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to update note:', error);
        alert('Failed to update note. Please try again.');
      },
    },
  });

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateNoteMutation.mutateAsync({
        highlightId,
        data: { note: noteText.trim() || null },
      });
    } finally {
      setIsSaving(false);
    }
  };

  const hasChanges = (noteText.trim() || null) !== (initialNote || null);
  const isLoading = disabled || isSaving;

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
            disabled={isLoading}
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
            <Button
              variant="text"
              size={'small'}
              onClick={handleSave}
              disabled={isLoading || !hasChanges}
              sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </Box>
        </Box>
      </Box>
    </Collapsable>
  );
};
