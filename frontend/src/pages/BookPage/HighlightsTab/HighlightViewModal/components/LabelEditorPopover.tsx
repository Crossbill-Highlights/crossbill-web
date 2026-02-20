import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  getGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGetQueryKey,
  useUpdateHighlightLabelApiV1HighlightLabelsStyleIdPatch,
} from '@/api/generated/highlight-labels/highlight-labels.ts';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { LABEL_COLORS } from '@/utils/colorUtils.ts';
import { Box, Popover, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { type MutableRefObject, useEffect, useRef, useState } from 'react';
import { CirclePicker, type ColorResult } from 'react-color';

interface LabelEditorContentProps {
  styleId: number;
  currentLabel?: string | null;
  currentColor?: string | null;
  bookId: number;
  submitRef: MutableRefObject<(() => void) | null>;
}

/**
 * Inner content component that remounts each time the popover opens,
 * ensuring labelText state resets from currentLabel prop.
 * Exposes handleLabelSubmit via submitRef so the outer Popover can
 * trigger a submit on close (before the content unmounts).
 */
const LabelEditorContent = ({
  styleId,
  currentLabel,
  currentColor,
  bookId,
  submitRef,
}: LabelEditorContentProps) => {
  const queryClient = useQueryClient();
  const { showSnackbar } = useSnackbar();
  const [labelText, setLabelText] = useState(currentLabel || '');

  const updateMutation = useUpdateHighlightLabelApiV1HighlightLabelsStyleIdPatch({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
        void queryClient.invalidateQueries({
          queryKey: getGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGetQueryKey(bookId),
        });
      },
      onError: (error: Error) => {
        console.error('Failed to update label:', error);
        showSnackbar('Failed to update label. Please try again.', 'error');
      },
    },
  });

  const handleLabelSubmit = () => {
    if (updateMutation.isPending) return;
    const trimmed = labelText.trim();
    if (trimmed !== (currentLabel || '')) {
      updateMutation.mutate({
        styleId,
        data: { label: trimmed || null },
      });
    }
  };

  // Expose submit to the outer Popover so it can call it before closing
  useEffect(() => {
    submitRef.current = handleLabelSubmit;
  });

  const handleColorChange = (color: ColorResult) => {
    updateMutation.mutate({
      styleId,
      data: { ui_color: color.hex },
    });
  };

  return (
    <Box sx={{ p: 2, width: 280 }}>
      <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
        Edit Label
      </Typography>
      <TextField
        value={labelText}
        onChange={(e) => setLabelText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            handleLabelSubmit();
          }
        }}
        placeholder="Label name..."
        size="small"
        fullWidth
        autoFocus
        sx={{ mb: 2 }}
      />
      <Typography variant="caption" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
        Color
      </Typography>
      <CirclePicker
        color={currentColor || undefined}
        colors={LABEL_COLORS}
        onChangeComplete={handleColorChange}
        width="100%"
      />
    </Box>
  );
};

interface LabelEditorPopoverProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
  styleId: number;
  currentLabel?: string | null;
  currentColor?: string | null;
  bookId: number;
}

export const LabelEditorPopover = ({
  anchorEl,
  open,
  onClose,
  styleId,
  currentLabel,
  currentColor,
  bookId,
}: LabelEditorPopoverProps) => {
  const submitRef = useRef<(() => void) | null>(null);

  const handleClose = () => {
    submitRef.current?.();
    onClose();
  };

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      transformOrigin={{ vertical: 'top', horizontal: 'left' }}
    >
      {open && (
        <LabelEditorContent
          styleId={styleId}
          currentLabel={currentLabel}
          currentColor={currentColor}
          bookId={bookId}
          submitRef={submitRef}
        />
      )}
    </Popover>
  );
};
