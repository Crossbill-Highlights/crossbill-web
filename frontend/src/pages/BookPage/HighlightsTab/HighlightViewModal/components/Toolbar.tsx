import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  useCreateBookmarkApiV1BooksBookIdBookmarksPost,
  useDeleteBookmarkApiV1BooksBookIdBookmarksBookmarkIdDelete,
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
} from '@/components/Icons.tsx';
import { ToolbarIconButton } from '@/components/ToolbarIconButton';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { Box } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface ToolbarProps {
  highlightId: number;
  bookId: number;
  highlightText: string;
  bookmark?: Bookmark;
  noteVisible: boolean;
  onNoteToggle: () => void;
  flashcardVisible: boolean;
  onFlashcardToggle: () => void;
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
  flashcardVisible,
  onFlashcardToggle,
  onDelete,
  disabled = false,
}: ToolbarProps) => {
  const { showSnackbar } = useSnackbar();
  const { handleBookmarkToggle, isProcessing } = useBookmarkMutations(
    bookmark,
    bookId,
    highlightId,
    showSnackbar
  );

  const handleCopyLink = async () => {
    const url = new URL(window.location.href);
    url.searchParams.set('highlightId', highlightId.toString());
    await navigator.clipboard.writeText(url.toString());
  };

  const handleCopyContent = async () => {
    await navigator.clipboard.writeText(highlightText);
  };

  const isDisabled = disabled || isProcessing;

  return (
    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
      <ToolbarIconButton
        title="Copy link"
        onClick={handleCopyLink}
        disabled={isDisabled}
        ariaLabel="Copy link to highlight"
        icon={<LinkIcon />}
      />
      <ToolbarIconButton
        title="Copy highlight content"
        onClick={handleCopyContent}
        disabled={isDisabled}
        ariaLabel="Copy highlight text"
        icon={<CopyIcon />}
      />
      <ToolbarIconButton
        title={bookmark ? 'Remove bookmark' : 'Add bookmark'}
        onClick={handleBookmarkToggle}
        disabled={isDisabled}
        ariaLabel={bookmark ? 'Remove bookmark' : 'Add bookmark'}
        icon={bookmark ? <BookmarkFilledIcon /> : <BookmarkIcon />}
      />
      <ToolbarIconButton
        title={noteVisible ? 'Hide note' : 'Show note'}
        onClick={onNoteToggle}
        disabled={isDisabled}
        ariaLabel={noteVisible ? 'Hide note' : 'Show note'}
        icon={<NotesIcon />}
      />
      <ToolbarIconButton
        title={flashcardVisible ? 'Hide flashcards' : 'Show flashcards'}
        onClick={onFlashcardToggle}
        disabled={isDisabled}
        ariaLabel={flashcardVisible ? 'Hide flashcards' : 'Show flashcards'}
        icon={<FlashcardsIcon />}
      />
      <ToolbarIconButton
        title="Delete highlight"
        onClick={onDelete}
        disabled={isDisabled}
        ariaLabel="Delete highlight"
        icon={<DeleteIcon />}
      />
    </Box>
  );
};

const useBookmarkMutations = (
  bookmark: Bookmark | undefined,
  bookId: number,
  highlightId: number,
  showSnackbar: (message: string, severity: 'error' | 'warning' | 'info' | 'success') => void
) => {
  const queryClient = useQueryClient();
  const [isProcessing, setIsProcessing] = useState(false);

  const createBookmarkMutation = useCreateBookmarkApiV1BooksBookIdBookmarksPost({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to create bookmark:', error);
        showSnackbar('Failed to create bookmark. Please try again.', 'error');
      },
    },
  });

  const deleteBookmarkMutation = useDeleteBookmarkApiV1BooksBookIdBookmarksBookmarkIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to delete bookmark:', error);
        showSnackbar('Failed to delete bookmark. Please try again.', 'error');
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

  return {
    isProcessing,
    handleBookmarkToggle,
  };
};
