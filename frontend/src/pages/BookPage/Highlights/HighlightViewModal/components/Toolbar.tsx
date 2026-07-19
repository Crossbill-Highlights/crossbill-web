import {
  useCreateBookmarkApiV1BooksBookIdBookmarksPost,
  useDeleteBookmarkApiV1BooksBookIdBookmarksBookmarkIdDelete,
} from '@/api/generated/bookmarks/bookmarks.ts';
import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import type { Bookmark } from '@/api/generated/model';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { DialogToolbar } from '@/components/dialogs/DialogToolbar.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import {
  BookmarkFilledIcon,
  BookmarkIcon,
  CopyIcon,
  DeleteIcon,
  LinkIcon,
} from '@/theme/Icons.tsx';
import { copyUrlWithSearchParam } from '@/utils/clipboard.ts';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface ToolbarProps {
  highlightId: number;
  bookId: number;
  highlightText: string;
  bookmark?: Bookmark;
  onDelete: () => void;
  disabled?: boolean;
}

export const Toolbar = ({
  highlightId,
  bookId,
  highlightText,
  bookmark,
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

  // Copy a link that works from any context: `highlightId` is only a validated
  // search param on the highlights route, so build the URL on that route —
  // copying the current URL from e.g. the chapter dialog would be a dead link.
  const handleCopyLink = async () => {
    await copyUrlWithSearchParam(
      'highlightId',
      highlightId,
      `${window.location.origin}/book/${bookId}/highlights`
    );
  };

  const handleCopyContent = async () => {
    await navigator.clipboard.writeText(highlightText);
  };

  const isDisabled = disabled || isProcessing;

  return (
    <DialogToolbar>
      <IconButtonWithTooltip
        title="Copy link"
        onClick={handleCopyLink}
        disabled={isDisabled}
        ariaLabel="Copy link to highlight"
        icon={<LinkIcon />}
      />
      <IconButtonWithTooltip
        title="Copy highlight content"
        onClick={handleCopyContent}
        disabled={isDisabled}
        ariaLabel="Copy highlight text"
        icon={<CopyIcon />}
      />
      <IconButtonWithTooltip
        title={bookmark ? 'Remove bookmark' : 'Add bookmark'}
        onClick={handleBookmarkToggle}
        disabled={isDisabled}
        ariaLabel={bookmark ? 'Remove bookmark' : 'Add bookmark'}
        icon={bookmark ? <BookmarkFilledIcon /> : <BookmarkIcon />}
      />
      <IconButtonWithTooltip
        title="Delete highlight"
        onClick={onDelete}
        disabled={isDisabled}
        ariaLabel="Delete highlight"
        icon={<DeleteIcon />}
      />
    </DialogToolbar>
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
      onError: (error: Error) => {
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
      onError: (error: Error) => {
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
