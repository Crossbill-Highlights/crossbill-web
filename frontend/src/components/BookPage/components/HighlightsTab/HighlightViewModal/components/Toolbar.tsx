import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  useCreateBookmarkApiV1BooksBookIdBookmarkPost,
  useDeleteBookmarkApiV1BooksBookIdBookmarkBookmarkIdDelete,
} from '@/api/generated/books/books.ts';
import type { Bookmark } from '@/api/generated/model';
import {
  BookmarkFilledIcon,
  BookmarkIcon,
  CopyIcon,
  DeleteIcon,
  FlashcardsIcon,
  LinkIcon,
  NotesIcon,
} from '@/components/common/Icons.tsx';
import { Box, IconButton, Tooltip } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface ToolbarProps {
  highlightId: number;
  bookId: number;
  highlightText: string;
  bookmark?: Bookmark;
  noteVisible: boolean;
  onNoteToggle: () => void;
  flashcardVisible?: boolean;
  onFlashcardToggle?: () => void;
  onDelete: () => void;
  disabled?: boolean;
}

export const Toolbar = ({
  highlightId,
  bookId,
  highlightText,
  bookmark,
  noteVisible,
  onNoteToggle,
  flashcardVisible = false,
  onFlashcardToggle,
  onDelete,
  disabled = false,
}: ToolbarProps) => {
  const queryClient = useQueryClient();
  const [isProcessing, setIsProcessing] = useState(false);

  const createBookmarkMutation = useCreateBookmarkApiV1BooksBookIdBookmarkPost({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to create bookmark:', error);
        alert('Failed to create bookmark. Please try again.');
      },
    },
  });

  const deleteBookmarkMutation = useDeleteBookmarkApiV1BooksBookIdBookmarkBookmarkIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to delete bookmark:', error);
        alert('Failed to delete bookmark. Please try again.');
      },
    },
  });

  const handleBookmarkToggle = async () => {
    setIsProcessing(true);
    try {
      if (bookmark) {
        // Remove bookmark
        await deleteBookmarkMutation.mutateAsync({
          bookId,
          bookmarkId: bookmark.id,
        });
      } else {
        // Create bookmark
        await createBookmarkMutation.mutateAsync({
          bookId,
          data: { highlight_id: highlightId },
        });
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCopyLink = async () => {
    const url = new URL(window.location.href);
    url.searchParams.set('highlightId', highlightId.toString());
    await navigator.clipboard.writeText(url.toString());
  };

  const handleCopyContent = async () => {
    await navigator.clipboard.writeText(highlightText);
  };

  const isLoading = disabled || isProcessing;

  return (
    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
      <Tooltip title="Copy link">
        <IconButton
          onClick={handleCopyLink}
          disabled={isLoading}
          aria-label="Copy link to highlight"
          size="small"
        >
          <LinkIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Copy highlight content">
        <IconButton
          onClick={handleCopyContent}
          disabled={isLoading}
          aria-label="Copy highlight text"
          size="small"
        >
          <CopyIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title={bookmark ? 'Remove bookmark' : 'Add bookmark'}>
        <IconButton
          onClick={handleBookmarkToggle}
          disabled={isLoading}
          aria-label={bookmark ? 'Remove bookmark' : 'Add bookmark'}
          size="small"
        >
          {bookmark ? <BookmarkFilledIcon /> : <BookmarkIcon />}
        </IconButton>
      </Tooltip>
      <Tooltip title={noteVisible ? 'Hide note' : 'Show note'}>
        <IconButton
          onClick={onNoteToggle}
          disabled={isLoading}
          aria-label={noteVisible ? 'Hide note' : 'Show note'}
          size="small"
        >
          <NotesIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title={flashcardVisible ? 'Hide flashcards' : 'Show flashcards'}>
        <IconButton
          onClick={onFlashcardToggle}
          disabled={isLoading}
          aria-label={flashcardVisible ? 'Hide flashcards' : 'Show flashcards'}
          size="small"
        >
          <FlashcardsIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Delete highlight">
        <IconButton
          onClick={onDelete}
          disabled={isLoading}
          aria-label="Delete highlight"
          size="small"
        >
          <DeleteIcon />
        </IconButton>
      </Tooltip>
    </Box>
  );
};
