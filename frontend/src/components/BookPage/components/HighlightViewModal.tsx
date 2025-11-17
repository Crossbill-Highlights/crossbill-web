import {
  useAddTagToHighlightApiV1BookBookIdHighlightHighlightIdTagPost,
  useDeleteHighlightsApiV1BookBookIdHighlightDelete,
  useRemoveTagFromHighlightApiV1BookBookIdHighlightHighlightIdTagTagIdDelete,
} from '@/api/generated/books/books';
import { useUpdateHighlightNoteApiV1HighlightsHighlightIdNotePost } from '@/api/generated/highlights/highlights';
import type { Highlight, HighlightTagInBook } from '@/api/generated/model';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import {
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  CalendarMonth as CalendarIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  FormatQuote as QuoteIcon,
} from '@mui/icons-material';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Autocomplete,
  Box,
  Button,
  Chip,
  IconButton,
  TextField,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';
import { useSwipeable } from 'react-swipeable';
import { CommonDialog } from '../../common/CommonDialog';

interface HighlightNoteProps {
  highlightId: number;
  bookId: number;
  initialNote: string | null | undefined;
  disabled?: boolean;
}

const HighlightNote = ({
  highlightId,
  bookId,
  initialNote,
  disabled = false,
}: HighlightNoteProps) => {
  const queryClient = useQueryClient();
  const [noteText, setNoteText] = useState<string>(initialNote || '');
  const [isSaving, setIsSaving] = useState(false);
  const [isExpanded, setIsExpanded] = useState(!!initialNote);

  // Update note when initialNote changes
  useEffect(() => {
    setNoteText(initialNote || '');
    setIsExpanded(!!initialNote);
  }, [initialNote]);

  const updateNoteMutation = useUpdateHighlightNoteApiV1HighlightsHighlightIdNotePost({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}`],
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
    <Accordion
      expanded={isExpanded}
      onChange={(_, expanded) => setIsExpanded(expanded)}
      sx={{
        backgroundColor: 'transparent',
        boxShadow: 'none',
        '&:before': { display: 'none' },
        '&.Mui-expanded': { margin: 0 },
      }}
    >
      <AccordionSummary
        sx={{
          minHeight: 'auto',
          padding: 0,
          '&.Mui-expanded': { minHeight: 'auto' },
          '& .MuiAccordionSummary-content': {
            margin: '8px 0',
            '&.Mui-expanded': { margin: '8px 0' },
          },
          '& .MuiAccordionSummary-expandIconWrapper': {
            display: 'none',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Note
          </Typography>
          <ExpandMoreIcon
            sx={{
              fontSize: 20,
              color: 'text.secondary',
              transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s',
            }}
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ padding: 0, paddingTop: 1 }}>
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
      </AccordionDetails>
    </Accordion>
  );
};

interface TagInputProps {
  highlightId: number;
  bookId: number;
  initialTags: HighlightTagInBook[];
  availableTags: HighlightTagInBook[];
  disabled?: boolean;
}

const TagInput = ({
  highlightId,
  bookId,
  initialTags,
  availableTags,
  disabled = false,
}: TagInputProps) => {
  const queryClient = useQueryClient();
  const [currentTags, setCurrentTags] = useState<HighlightTagInBook[]>(initialTags);
  const [isProcessing, setIsProcessing] = useState(false);

  // Update tags when initialTags changes
  useEffect(() => {
    setCurrentTags(initialTags);
  }, [initialTags]);

  // Mutation hooks
  const addTagMutation = useAddTagToHighlightApiV1BookBookIdHighlightHighlightIdTagPost({
    mutation: {
      onSuccess: (data) => {
        setCurrentTags(data.highlight_tags || []);
        void queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}`],
        });
        void queryClient.invalidateQueries({
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
          void queryClient.invalidateQueries({
            queryKey: [`/api/v1/book/${bookId}`],
          });
          void queryClient.invalidateQueries({
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
        highlightId,
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
        highlightId,
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

  const isLoading = disabled || isProcessing;

  return (
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
        renderValue={(tagValue, getTagProps) =>
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
  );
};

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

  const hasNavigation = allHighlights && allHighlights.length > 1 && onNavigate;
  const hasPrevious = hasNavigation && currentIndex > 0;
  const hasNext = hasNavigation && currentIndex < allHighlights.length - 1;

  const startsWithLowercase =
    highlight.text.length > 0 &&
    highlight.text[0] === highlight.text[0].toLowerCase() &&
    highlight.text[0] !== highlight.text[0].toUpperCase();

  // Helper function to render highlight text as paragraphs
  const renderHighlightText = () => {
    const prefix = startsWithLowercase ? '...' : '';
    // Split by newlines and filter out empty strings
    const paragraphs = highlight.text.split('\n').filter((p) => p.trim() !== '');

    return (
      <>
        {paragraphs.map((paragraph, index) => (
          <Typography
            key={index}
            component="p"
            variant="h6"
            sx={{
              fontWeight: 500,
              color: 'text.primary',
              lineHeight: 1.7,
              fontSize: '1.25rem',
              margin: 0,
              marginBottom: index < paragraphs.length - 1 ? 2 : 0,
            }}
          >
            {index === 0 ? prefix + paragraph : paragraph}
          </Typography>
        ))}
      </>
    );
  };

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

  // Swipe navigation
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => {
      if (hasNext) handleNext();
    },
    onSwipedRight: () => {
      if (hasPrevious) handlePrevious();
    },
    swipeDuration: 500,
    preventScrollOnSwipe: false,
  });

  const deleteHighlightMutation = useDeleteHighlightsApiV1BookBookIdHighlightDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.refetchQueries({
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
    void queryClient.invalidateQueries({
      queryKey: [`/api/v1/book/${bookId}`],
    });
    void queryClient.invalidateQueries({
      queryKey: [`/api/v1/book/${bookId}/highlight_tags`],
    });
    onClose();
  };

  const isDeleting = deleteHighlightMutation.isPending;
  const isLoading = isDeleting;

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
        <Box display="flex" flexDirection="column" gap={3} flex={1} {...swipeHandlers}>
          {/* Highlight Text */}
          <FadeInOut ekey={highlight.id}>
            <Box display="flex" flexDirection="column" gap={3} flex={1}>
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
                <Box sx={{ flex: 1 }}>{renderHighlightText()}</Box>
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
            </Box>
          </FadeInOut>
          <TagInput
            highlightId={highlight.id}
            bookId={bookId}
            initialTags={highlight.highlight_tags || []}
            availableTags={availableTags}
            disabled={isLoading}
          />
          <HighlightNote
            highlightId={highlight.id}
            bookId={bookId}
            initialNote={highlight.note}
            disabled={isLoading}
          />
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
      <Box
        sx={{ display: { xs: 'flex', sm: 'none' }, flexDirection: 'column', gap: 3 }}
        {...swipeHandlers}
      >
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
          <Box sx={{ flex: 1 }}>{renderHighlightText()}</Box>
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

        <TagInput
          highlightId={highlight.id}
          bookId={bookId}
          initialTags={highlight.highlight_tags || []}
          availableTags={availableTags}
          disabled={isLoading}
        />
        <HighlightNote
          highlightId={highlight.id}
          bookId={bookId}
          initialNote={highlight.note}
          disabled={isLoading}
        />

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
