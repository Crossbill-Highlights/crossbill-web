import {
  useAddTagToHighlightApiV1BookBookIdHighlightHighlightIdTagPost,
  useDeleteHighlightsApiV1BookBookIdHighlightDelete,
  useRemoveTagFromHighlightApiV1BookBookIdHighlightHighlightIdTagTagIdDelete,
} from '@/api/generated/books/books';
import type { Highlight, HighlightTagInBook } from '@/api/generated/model';
import {
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  CalendarMonth as CalendarIcon,
  Delete as DeleteIcon,
  FormatQuote as QuoteIcon,
} from '@mui/icons-material';
import { Autocomplete, Box, Button, Chip, IconButton, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';
import { CommonDialog } from '../../common/CommonDialog';

interface HighlightViewModalProps {
  highlight: Highlight;
  bookId: number;
  open: boolean;
  onClose: () => void;
  availableTags: HighlightTagInBook[];
  allHighlights?: Highlight[];
  currentIndex?: number;
  onNavigate?: (newIndex: number) => void;
}

export const HighlightViewModal = ({
  highlight,
  bookId,
  open,
  onClose,
  availableTags,
  allHighlights,
  currentIndex = 0,
  onNavigate,
}: HighlightViewModalProps) => {
  const queryClient = useQueryClient();
  const [currentTags, setCurrentTags] = useState<HighlightTagInBook[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const hasNavigation = allHighlights && allHighlights.length > 1 && onNavigate;
  const hasPrevious = hasNavigation && currentIndex > 0;
  const hasNext = hasNavigation && currentIndex < allHighlights.length - 1;

  const startsWithLowercase =
    highlight.text.length > 0 &&
    highlight.text[0] === highlight.text[0].toLowerCase() &&
    highlight.text[0] !== highlight.text[0].toUpperCase();
  const formattedText = startsWithLowercase ? `...${highlight.text}` : highlight.text;

  const handlePrevious = useCallback(() => {
    if (hasPrevious && onNavigate) {
      onNavigate(currentIndex - 1);
    }
  }, [currentIndex, hasPrevious, onNavigate]);

  const handleNext = useCallback(() => {
    if (hasNext && onNavigate) {
      onNavigate(currentIndex + 1);
    }
  }, [currentIndex, hasNext, onNavigate]);

  // Initialize current tags when dialog opens or highlight changes
  useEffect(() => {
    if (open && highlight.highlight_tags) {
      setCurrentTags(highlight.highlight_tags);
    }
  }, [open, highlight.highlight_tags]);

  // Keyboard navigation
  useEffect(() => {
    if (!open || !hasNavigation) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && hasPrevious) {
        e.preventDefault();
        handlePrevious();
      } else if (e.key === 'ArrowRight' && hasNext) {
        e.preventDefault();
        handleNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, hasNavigation, hasPrevious, hasNext, currentIndex, handlePrevious, handleNext]);

  // Mutation hooks
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

  const removeTagMutation =
    useRemoveTagFromHighlightApiV1BookBookIdHighlightHighlightIdTagTagIdDelete({
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

  const deleteHighlightMutation = useDeleteHighlightsApiV1BookBookIdHighlightDelete({
    mutation: {
      onSuccess: () => {
        queryClient.refetchQueries({
          queryKey: [`/api/v1/book/${bookId}`],
          exact: true,
        });
        onClose();
      },
      onError: (error) => {
        console.error('Failed to delete highlight:', error);
        alert('Failed to delete highlight. Please try again.');
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

  const handleDelete = () => {
    if (
      confirm(
        'Are you sure you want to delete this highlight? This will soft-delete the highlight and prevent it from being recreated during sync.'
      )
    ) {
      deleteHighlightMutation.mutate({
        bookId,
        data: { highlight_ids: [highlight.id] },
      });
    }
  };

  const handleClose = () => {
    queryClient.invalidateQueries({
      queryKey: [`/api/v1/book/${bookId}`],
    });
    queryClient.invalidateQueries({
      queryKey: [`/api/v1/book/${bookId}/highlight_tags`],
    });
    onClose();
  };

  const isDeleting = deleteHighlightMutation.isPending;
  const isLoading = isProcessing || isDeleting;

  return (
    <CommonDialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      isLoading={isLoading}
      title="View Highlight"
      footerActions={
        <>
          <Button
            onClick={handleDelete}
            color="error"
            startIcon={<DeleteIcon />}
            disabled={isLoading}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
          <Button onClick={handleClose} disabled={isLoading}>
            Close
          </Button>
        </>
      }
    >
      {/* Desktop Layout: Navigation buttons on sides */}
      <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'center', gap: 2 }}>
        {/* Previous Button (Desktop) */}
        {hasNavigation && (
          <IconButton
            onClick={handlePrevious}
            disabled={!hasPrevious || isLoading}
            sx={{
              flexShrink: 0,
              visibility: hasPrevious ? 'visible' : 'hidden',
            }}
            aria-label="Previous highlight"
          >
            <ArrowBackIcon />
          </IconButton>
        )}

        {/* Main Content */}
        <Box display="flex" flexDirection="column" gap={3} flex={1}>
          {/* Highlight Text */}
          <Box sx={{ display: 'flex', alignItems: 'start', gap: 2 }}>
            <QuoteIcon
              sx={{
                fontSize: 28,
                color: 'primary.main',
                flexShrink: 0,
                mt: 0.5,
                opacity: 0.7,
              }}
            />
            <Typography
              variant="h6"
              sx={{
                fontWeight: 500,
                color: 'text.primary',
                lineHeight: 1.7,
                fontSize: '1.25rem',
              }}
            >
              {formattedText}
            </Typography>
          </Box>

          {/* Metadata */}
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', opacity: 0.8 }}>
            <CalendarIcon
              sx={{
                fontSize: 20,
                color: 'text.secondary',
              }}
            />
            <Typography variant="body2" color="text.secondary">
              {new Date(highlight.datetime).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
              {highlight.page && ` • Page ${highlight.page}`}
            </Typography>
          </Box>

          {/* Tags */}
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Tags
            </Typography>
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
                  placeholder="Add tags..."
                  helperText="Press Enter to add a tag, click X to remove"
                  disabled={isLoading}
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
                      disabled={isLoading}
                    />
                  );
                })
              }
              disabled={isLoading}
            />
          </Box>
        </Box>

        {/* Next Button (Desktop) */}
        {hasNavigation && (
          <IconButton
            onClick={handleNext}
            disabled={!hasNext || isLoading}
            sx={{
              flexShrink: 0,
              visibility: hasNext ? 'visible' : 'hidden',
            }}
            aria-label="Next highlight"
          >
            <ArrowForwardIcon />
          </IconButton>
        )}
      </Box>

      {/* Mobile Layout: Navigation buttons below tags */}
      <Box sx={{ display: { xs: 'flex', sm: 'none' }, flexDirection: 'column', gap: 3 }}>
        {/* Highlight Text */}
        <Box sx={{ display: 'flex', alignItems: 'start', gap: 2 }}>
          <QuoteIcon
            sx={{
              fontSize: 28,
              color: 'primary.main',
              flexShrink: 0,
              mt: 0.5,
              opacity: 0.7,
            }}
          />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 500,
              color: 'text.primary',
              lineHeight: 1.7,
              fontSize: '1.25rem',
            }}
          >
            {formattedText}
          </Typography>
        </Box>

        {/* Metadata */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', opacity: 0.8 }}>
          <CalendarIcon
            sx={{
              fontSize: 20,
              color: 'text.secondary',
            }}
          />
          <Typography variant="body2" color="text.secondary">
            {new Date(highlight.datetime).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
            {highlight.page && ` • Page ${highlight.page}`}
          </Typography>
        </Box>

        {/* Tags */}
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Tags
          </Typography>
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
                placeholder="Add tags..."
                helperText="Press Enter to add a tag, click X to remove"
                disabled={isLoading}
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
                    disabled={isLoading}
                  />
                );
              })
            }
            disabled={isLoading}
          />
        </Box>

        {/* Navigation Buttons (Mobile) */}
        {hasNavigation && (
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, pt: 1 }}>
            <Button
              onClick={handlePrevious}
              disabled={!hasPrevious || isLoading}
              startIcon={<ArrowBackIcon />}
              variant="outlined"
              sx={{ flex: 1, maxWidth: '200px' }}
            >
              Previous
            </Button>
            <Button
              onClick={handleNext}
              disabled={!hasNext || isLoading}
              endIcon={<ArrowForwardIcon />}
              variant="outlined"
              sx={{ flex: 1, maxWidth: '200px' }}
            >
              Next
            </Button>
          </Box>
        )}
      </Box>
    </CommonDialog>
  );
};
