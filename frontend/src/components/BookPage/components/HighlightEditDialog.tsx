import type { Highlight, HighlightTagInBook } from '@/api/generated/model';
import {
  useAddTagToHighlightApiV1BookBookIdHighlightHighlightIdTagPost,
  useRemoveTagFromHighlightApiV1BookBookIdHighlightHighlightIdTagTagIdDelete,
} from '@/api/generated/books/books';
import { Close as CloseIcon, LocalOffer as TagIcon } from '@mui/icons-material';
import {
  Autocomplete,
  Box,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

interface HighlightTagInputProps {
  highlight: Highlight;
  bookId: number;
  availableTags: HighlightTagInBook[];
}

const HighlightTagInput = ({ highlight, bookId, availableTags }: HighlightTagInputProps) => {
  const queryClient = useQueryClient();
  const [currentTags, setCurrentTags] = useState<HighlightTagInBook[]>(
    highlight.highlight_tags || []
  );
  const [isProcessing, setIsProcessing] = useState(false);

  // Update current tags when highlight changes
  useEffect(() => {
    setCurrentTags(highlight.highlight_tags || []);
  }, [highlight.highlight_tags]);

  const addTagMutation = useAddTagToHighlightApiV1BookBookIdHighlightHighlightIdTagPost({
    mutation: {
      onSuccess: (data) => {
        setCurrentTags(data.highlight_tags || []);
        queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}`],
        });
        queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}/highlight_tags`],
        });
      },
      onError: (error) => {
        console.error('Failed to add tag:', error);
        alert('Failed to add tag. Please try again.');
      },
    },
  });

  const removeTagMutation = useRemoveTagFromHighlightApiV1BookBookIdHighlightHighlightIdTagTagIdDelete({
    mutation: {
      onSuccess: (data) => {
        setCurrentTags(data.highlight_tags || []);
        queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}`],
        });
        queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}/highlight_tags`],
        });
      },
      onError: (error) => {
        console.error('Failed to remove tag:', error);
        alert('Failed to remove tag. Please try again.');
      },
    },
  });

  const addTagToHighlight = async (tagName: string) => {
    setIsProcessing(true);
    try {
      await addTagMutation.mutateAsync({
        bookId,
        highlightId: highlight.id,
        data: { name: tagName },
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const removeTagFromHighlight = async (tagId: number) => {
    setIsProcessing(true);
    try {
      await removeTagMutation.mutateAsync({
        bookId,
        highlightId: highlight.id,
        tagId,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTagChange = async (
    _: React.SyntheticEvent,
    newValue: (HighlightTagInBook | string)[]
  ) => {
    const currentTagNames = currentTags.map((t) => t.name);
    const newTagNames = newValue.map((v) => (typeof v === 'string' ? v : v.name));

    // Find tags that were added
    const addedTags = newTagNames.filter((name) => !currentTagNames.includes(name));

    // Find tags that were removed
    const removedTags = currentTags.filter((tag) => !newTagNames.includes(tag.name));

    // Process additions
    for (const tagName of addedTags) {
      await addTagToHighlight(tagName);
    }

    // Process removals
    for (const tag of removedTags) {
      await removeTagFromHighlight(tag.id);
    }
  };

  return (
    <Autocomplete
      multiple
      freeSolo
      options={availableTags}
      getOptionLabel={(option) => (typeof option === 'string' ? option : option.name)}
      value={currentTags}
      onChange={handleTagChange}
      isOptionEqualToValue={(option, value) => {
        if (typeof option === 'string' || typeof value === 'string') {
          return option === value;
        }
        return option.id === value.id;
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Tags"
          placeholder="Add tags..."
          helperText="Press Enter to add a tag, click X to remove"
          disabled={isProcessing}
        />
      )}
      renderTags={(tagValue, getTagProps) =>
        tagValue.map((option, index) => {
          const { key, ...tagProps } = getTagProps({ index });
          return (
            <Chip
              key={key}
              label={typeof option === 'string' ? option : option.name}
              {...tagProps}
              disabled={isProcessing}
            />
          );
        })
      }
      disabled={isProcessing}
    />
  );
};

interface HighlightEditDialogProps {
  highlight: Highlight;
  bookId: number;
  open: boolean;
  onClose: () => void;
  availableTags: HighlightTagInBook[];
}

export const HighlightEditDialog = ({
  highlight,
  bookId,
  open,
  onClose,
  availableTags,
}: HighlightEditDialogProps) => {
  const queryClient = useQueryClient();

  const handleClose = () => {
    // Final refresh when closing the dialog
    queryClient.invalidateQueries({
      queryKey: [`/api/v1/book/${bookId}`],
    });
    queryClient.invalidateQueries({
      queryKey: [`/api/v1/book/${bookId}/highlight_tags`],
    });
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <TagIcon />
            <span>Manage Tags</span>
          </Box>
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleClose}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box display="flex" flexDirection="column" gap={3}>
          {/* Highlight Preview */}
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Highlight:
            </Typography>
            <Typography variant="body1" sx={{ fontStyle: 'italic', pl: 2 }}>
              "{highlight.text.substring(0, 200)}
              {highlight.text.length > 200 ? '...' : ''}"
            </Typography>
          </Box>

          {/* Tag Input */}
          <Box>
            <HighlightTagInput
              highlight={highlight}
              bookId={bookId}
              availableTags={availableTags}
            />
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};
