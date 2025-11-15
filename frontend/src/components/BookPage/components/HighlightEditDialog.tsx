import type { Highlight, HighlightTagInBook } from '@/api/generated/model';
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
  const [currentTags, setCurrentTags] = useState<HighlightTagInBook[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Initialize current tags when dialog opens or highlight changes
  useEffect(() => {
    if (open && highlight.highlight_tags) {
      setCurrentTags(highlight.highlight_tags);
    }
  }, [open, highlight.highlight_tags]);

  const addTagToHighlight = async (tagName: string) => {
    setIsProcessing(true);
    try {
      const response = await fetch(
        `/api/v1/book/${bookId}/highlight/${highlight.id}/tag`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ name: tagName }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to add tag');
      }

      const updatedHighlight = await response.json();
      setCurrentTags(updatedHighlight.highlight_tags || []);

      // Invalidate queries to refresh the UI
      await queryClient.invalidateQueries({
        queryKey: [`/api/v1/book/${bookId}`],
      });
      await queryClient.invalidateQueries({
        queryKey: [`/api/v1/book/${bookId}/highlight_tags`],
      });
    } catch (error) {
      console.error('Failed to add tag:', error);
      alert('Failed to add tag. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const removeTagFromHighlight = async (tagId: number) => {
    setIsProcessing(true);
    try {
      const response = await fetch(
        `/api/v1/book/${bookId}/highlight/${highlight.id}/tag/${tagId}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to remove tag');
      }

      const updatedHighlight = await response.json();
      setCurrentTags(updatedHighlight.highlight_tags || []);

      // Invalidate queries to refresh the UI
      await queryClient.invalidateQueries({
        queryKey: [`/api/v1/book/${bookId}`],
      });
      await queryClient.invalidateQueries({
        queryKey: [`/api/v1/book/${bookId}/highlight_tags`],
      });
    } catch (error) {
      console.error('Failed to remove tag:', error);
      alert('Failed to remove tag. Please try again.');
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
            disabled={isProcessing}
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
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};
