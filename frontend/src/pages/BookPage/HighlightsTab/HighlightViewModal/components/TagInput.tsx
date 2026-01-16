import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey,
  useAddTagToHighlightApiV1BooksBookIdHighlightHighlightIdTagPost,
  useRemoveTagFromHighlightApiV1BooksBookIdHighlightHighlightIdTagTagIdDelete,
} from '@/api/generated/books/books.ts';
import type { HighlightTagInBook } from '@/api/generated/model';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { Autocomplete, Box, Chip, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

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
  const { showSnackbar } = useSnackbar();
  const { isProcessing, currentTags, updateTagList } = useTagState(
    bookId,
    highlightId,
    initialTags,
    showSnackbar
  );

  const isDisabled = disabled || isProcessing;

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
        onChange={(_, value) => updateTagList(value)}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        renderInput={(params) => (
          <TextField
            {...params}
            placeholder="Add tags..."
            helperText="Press Enter to add a tag, click X to remove"
            disabled={isDisabled}
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
                disabled={isDisabled}
              />
            );
          })
        }
        disabled={isDisabled}
      />
    </Box>
  );
};

const useTagState = (
  bookId: number,
  highlightId: number,
  initialTags: HighlightTagInBook[],
  showSnackbar: (message: string, severity: 'error' | 'warning' | 'info' | 'success') => void
) => {
  const queryClient = useQueryClient();
  const [currentTags, setCurrentTags] = useState<HighlightTagInBook[]>(initialTags);
  const [isProcessing, setIsProcessing] = useState(false);

  const addTagMutation = useAddTagToHighlightApiV1BooksBookIdHighlightHighlightIdTagPost({
    mutation: {
      onSuccess: (data) => {
        setCurrentTags(data.highlight_tags);
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
        void queryClient.invalidateQueries({
          queryKey: getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to add tag:', error);
        showSnackbar('Failed to add tag. Please try again.', 'error');
      },
    },
  });

  const removeTagMutation =
    useRemoveTagFromHighlightApiV1BooksBookIdHighlightHighlightIdTagTagIdDelete({
      mutation: {
        onSuccess: (data) => {
          setCurrentTags(data.highlight_tags);
          void queryClient.invalidateQueries({
            queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
          });
          void queryClient.invalidateQueries({
            queryKey: getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey(bookId),
          });
        },
        onError: (error) => {
          console.error('Failed to remove tag:', error);
          showSnackbar('Failed to remove tag. Please try again.', 'error');
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

  const updateTagList = async (newValue: (HighlightTagInBook | string)[]) => {
    const currentTagNames = currentTags.map((t) => t.name);
    const newTagNames = newValue.map((v) => (typeof v === 'string' ? v : v.name));

    const addedTags = newTagNames.filter((name) => !currentTagNames.includes(name));
    const removedTags = currentTags.filter((tag) => !newTagNames.includes(tag.name));

    for (const tagName of addedTags) {
      await addTagToHighlight(tagName);
    }

    for (const tag of removedTags) {
      await removeTagFromHighlight(tag.id);
    }
  };

  return {
    isProcessing,
    currentTags,
    updateTagList,
  };
};
