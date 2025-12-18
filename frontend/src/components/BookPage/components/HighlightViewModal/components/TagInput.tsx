import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey,
  useAddTagToHighlightApiV1BooksBookIdHighlightHighlightIdTagPost,
  useRemoveTagFromHighlightApiV1BooksBookIdHighlightHighlightIdTagTagIdDelete,
} from '@/api/generated/books/books';
import type { HighlightTagInBook } from '@/api/generated/model';
import { Autocomplete, Box, Chip, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

interface TagInputProps {
  highlightId: number;
  bookId: number;
  initialTags: HighlightTagInBook[];
  availableTags: HighlightTagInBook[];
  disabled?: boolean;
}

export const TagInput = ({
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
  const addTagMutation = useAddTagToHighlightApiV1BooksBookIdHighlightHighlightIdTagPost({
    mutation: {
      onSuccess: (data) => {
        setCurrentTags(data.highlight_tags || []);
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
        void queryClient.invalidateQueries({
          queryKey: getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to add tag:', error);
        alert('Failed to add tag. Please try again.');
      },
    },
  });

  const removeTagMutation =
    useRemoveTagFromHighlightApiV1BooksBookIdHighlightHighlightIdTagTagIdDelete({
      mutation: {
        onSuccess: (data) => {
          setCurrentTags(data.highlight_tags || []);
          void queryClient.invalidateQueries({
            queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
          });
          void queryClient.invalidateQueries({
            queryKey: getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey(bookId),
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
