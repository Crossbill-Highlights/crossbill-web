import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey,
  useDeleteHighlightsApiV1BooksBookIdHighlightDelete,
} from '@/api/generated/highlights/highlights.ts';
import type { Bookmark, Highlight, HighlightTagInBook } from '@/api/generated/model';
import { FadeInOut } from '@/components/animations/FadeInOut.tsx';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { CommonDialogHorizontalNavigation } from '@/components/dialogs/CommonDialogHorizontalNavigation.tsx';
import { CommonDialogTitle } from '@/components/dialogs/CommonDialogTitle.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useModalHorizontalNavigation } from '@/components/dialogs/useModalHorizontalNavigation.ts';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { HighlightTagInput } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/components/HighlightTagInput.tsx';
import { useImmediateTagMutation } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/hooks/useImmediateTagMutation.ts';
import { Box, Button, Stack } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { HighlightContent } from '../../common/HighlightContent.tsx';
import { FlashcardSection } from './components/FlashcardSection.tsx';
import { HighlightNote } from './components/HighlightNote.tsx';
import { LabelEditorPopover } from './components/LabelEditorPopover.tsx';
import { ProgressBar } from './components/ProgressBar.tsx';
import { Toolbar } from './components/Toolbar.tsx';
import { useVisibilityToggle } from './hooks/useVisibilityToggle.ts';

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
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [labelAnchorEl, setLabelAnchorEl] = useState<HTMLElement | null>(null);

  const currentBookmark = bookmarksByHighlightId[highlight.id] ?? undefined;

  const { isProcessing, currentTags, updateTagList } = useImmediateTagMutation({
    bookId,
    highlightId: highlight.id,
    initialTags: highlight.highlight_tags,
    showSnackbar,
  });

  const { hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext, swipeHandlers } =
    useModalHorizontalNavigation({
      open,
      currentIndex,
      totalCount: allHighlights?.length ?? 1,
      onNavigate,
    });

  const { visible: noteVisible, toggle: handleNoteToggle } = useVisibilityToggle(
    highlight.id,
    !!highlight.note
  );
  const { visible: flashcardVisible, toggle: handleFlashcardToggle } = useVisibilityToggle(
    highlight.id,
    !!highlight.flashcards.length
  );

  const deleteHighlightMutation = useDeleteHighlightsApiV1BooksBookIdHighlightDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.refetchQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
          exact: true,
        });
        onClose();
      },
      onError: (error: Error) => {
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

  const handleLabelClick = (event: React.MouseEvent<HTMLElement>) => {
    if (highlight.label?.highlight_style_id) {
      setLabelAnchorEl(event.currentTarget);
    }
  };

  const isLoading = deleteHighlightMutation.isPending;

  const titleText = highlight.chapter ? `${highlight.chapter}` : 'Highlight';
  const title = <CommonDialogTitle>{titleText}</CommonDialogTitle>;

  // Shared content for both layouts
  const renderContent = () => (
    <Box key={highlight.id}>
      <Stack gap={2}>
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
        <HighlightTagInput
          value={currentTags}
          onChange={updateTagList}
          availableTags={availableTags}
          isProcessing={isProcessing}
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
          highlight={highlight}
          bookId={bookId}
          visible={flashcardVisible}
          disabled={isLoading}
        />
      </Stack>
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
      <CommonDialogHorizontalNavigation
        hasNavigation={hasNavigation}
        hasPrevious={hasPrevious}
        hasNext={hasNext}
        onPrevious={handlePrevious}
        onNext={handleNext}
        swipeHandlers={swipeHandlers}
        disabled={isLoading}
      >
        <FadeInOut ekey={highlight.id}>
          <HighlightContent highlight={highlight} onLabelClick={handleLabelClick} />
        </FadeInOut>
        {renderContent()}
      </CommonDialogHorizontalNavigation>

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

      {highlight.label?.highlight_style_id && (
        <LabelEditorPopover
          anchorEl={labelAnchorEl}
          open={!!labelAnchorEl}
          onClose={() => setLabelAnchorEl(null)}
          styleId={highlight.label.highlight_style_id}
          currentLabel={highlight.label.text}
          currentColor={highlight.label.ui_color}
          bookId={bookId}
        />
      )}
    </CommonDialog>
  );
};
