import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey,
  useDeleteHighlightsApiV1BooksBookIdHighlightDelete,
} from '@/api/generated/books/books.ts';
import type { Bookmark, Highlight, HighlightTagInBook } from '@/api/generated/model';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { ArrowBackIcon, ArrowForwardIcon } from '@/components/common/Icons.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { Box, Button, IconButton, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { CommonDialog } from '../../../common/CommonDialog.tsx';
import { ConfirmationDialog } from '../../../common/ConfirmationDialog.tsx';
import { HighlightContent } from '../../common/HighlightContent.tsx';
import { FlashcardSection } from './components/FlashcardSection.tsx';
import { HighlightNote } from './components/HighlightNote.tsx';
import { ProgressBar } from './components/ProgressBar.tsx';
import { TagInput } from './components/TagInput.tsx';
import { Toolbar } from './components/Toolbar.tsx';
import { useHighlightNavigation } from './hooks/useHighlightNavigation.ts';

export interface HighlightViewModalProps {
  highlight: Highlight;
  bookId: number;
  open: boolean;
  onClose: (lastViewedHighlightId?: number) => void;
  availableTags: HighlightTagInBook[];
  bookmarksByHighlightId: Record<number, Bookmark>;
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
  bookmarksByHighlightId,
  allHighlights,
  currentIndex = 0,
  onNavigate,
}: HighlightViewModalProps) => {
  const queryClient = useQueryClient();
  const { showSnackbar } = useSnackbar();
  const [noteVisibleWhenEmpty, setNoteVisibleWhenEmpty] = useState(false);
  const [flashcardVisibleWhenEmpty, setFlashcardVisibleWhenEmpty] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const currentBookmark = bookmarksByHighlightId[highlight.id] ?? undefined;

  const { hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext, swipeHandlers } =
    useHighlightNavigation({
      open,
      currentIndex,
      totalCount: allHighlights?.length ?? 1,
      onNavigate,
    });

  const hasNote = !!highlight.note;
  const noteVisible = hasNote || noteVisibleWhenEmpty;

  const hasFlashcards = !!highlight.flashcards.length;
  const flashcardVisible = hasFlashcards || flashcardVisibleWhenEmpty;

  const handleNoteToggle = () => {
    setNoteVisibleWhenEmpty((prev) => !prev);
  };

  const handleFlashcardToggle = () => {
    setFlashcardVisibleWhenEmpty((prev) => !prev);
  };

  const deleteHighlightMutation = useDeleteHighlightsApiV1BooksBookIdHighlightDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.refetchQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
          exact: true,
        });
        onClose();
      },
      onError: (error) => {
        console.error('Failed to delete highlight:', error);
        showSnackbar('Failed to delete highlight. Please try again.', 'error');
      },
    },
  });

  const handleDelete = () => {
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = () => {
    setDeleteConfirmOpen(false);
    deleteHighlightMutation.mutate({
      bookId,
      data: { highlight_ids: [highlight.id] },
    });
  };

  const handleClose = () => {
    void queryClient.invalidateQueries({
      queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
    });
    void queryClient.invalidateQueries({
      queryKey: getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey(bookId),
    });
    onClose(highlight.id);
  };

  const isLoading = deleteHighlightMutation.isPending;

  const titleText = highlight.chapter ? `${highlight.chapter}` : 'Highlight';
  const title = (
    <Typography
      variant="h6"
      component="span"
      sx={{
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        maxWidth: { xs: 'calc(100vw - 120px)', sm: 'calc(100vw - 200px)', md: '600px' },
        display: 'block',
      }}
    >
      {titleText}
    </Typography>
  );

  // Shared content for both layouts
  const renderContent = () => (
    <Box key={highlight.id}>
      <Toolbar
        highlightId={highlight.id}
        bookId={bookId}
        highlightText={highlight.text}
        bookmark={currentBookmark}
        noteVisible={noteVisible}
        onNoteToggle={handleNoteToggle}
        flashcardVisible={flashcardVisible}
        onFlashcardToggle={handleFlashcardToggle}
        onDelete={handleDelete}
        disabled={isLoading}
      />
      <TagInput
        highlightId={highlight.id}
        bookId={bookId}
        initialTags={highlight.highlight_tags}
        availableTags={availableTags}
        disabled={isLoading}
      />
      <HighlightNote
        highlightId={highlight.id}
        bookId={bookId}
        initialNote={highlight.note}
        visible={noteVisible}
        disabled={isLoading}
      />
      <FlashcardSection
        highlightId={highlight.id}
        bookId={bookId}
        flashcards={highlight.flashcards}
        visible={flashcardVisible}
        disabled={isLoading}
      />
    </Box>
  );

  return (
    <CommonDialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      isLoading={isLoading}
      title={title}
      headerElement={
        hasNavigation && allHighlights ? (
          <ProgressBar currentIndex={currentIndex} totalCount={allHighlights.length} />
        ) : undefined
      }
      footerActions={
        <Box sx={{ display: 'flex', justifyContent: 'end', width: '100%' }}>
          <Button onClick={handleClose} disabled={isLoading}>
            Close
          </Button>
        </Box>
      }
    >
      {/* Desktop Layout: Navigation buttons on sides */}
      <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'center', gap: 2 }}>
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

        <Box display="flex" flexDirection="column" gap={3} flex={1} {...swipeHandlers}>
          <FadeInOut ekey={highlight.id}>
            <HighlightContent highlight={highlight} />
          </FadeInOut>
          {renderContent()}
        </Box>

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

      {/* Mobile Layout: Navigation buttons below */}
      <Box
        sx={{ display: { xs: 'flex', sm: 'none' }, flexDirection: 'column', gap: 3 }}
        {...swipeHandlers}
      >
        <HighlightContent highlight={highlight} />
        {renderContent()}

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

      <ConfirmationDialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Highlight"
        message="Are you sure you want to delete this highlight?"
        confirmText="Delete"
        confirmColor="error"
        isLoading={isLoading}
      />
    </CommonDialog>
  );
};
