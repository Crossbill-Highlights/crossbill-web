import type { NoteWithLinks } from '@/api/generated/model';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { Box, Button } from '@mui/material';
import { useRef, useState } from 'react';

import { NoteEditorForm, type NoteEditorFormHandle } from './NoteEditorForm';

interface NoteEditorDialogProps {
  open: boolean;
  onClose: () => void;
  /** Edit mode when set; create mode otherwise */
  note?: NoteWithLinks | null;
  initialChapterIds?: number[];
  initialHighlightIds?: number[];
  initialBody?: string;
}

export const NoteEditorDialog = ({
  open,
  onClose,
  note,
  initialChapterIds,
  initialHighlightIds,
  initialBody,
}: NoteEditorDialogProps) => {
  const formRef = useRef<NoteEditorFormHandle>(null);
  const [status, setStatus] = useState({ isSaving: false, canSave: false });

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      title={note ? 'Edit Note' : 'New Note'}
      maxWidth="md"
      isLoading={status.isSaving}
      footerActions={
        <Box sx={{ display: 'flex', gap: 1, width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} disabled={status.isSaving}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={() => formRef.current?.submit()}
            disabled={!status.canSave}
          >
            {status.isSaving ? 'Saving...' : 'Save'}
          </Button>
        </Box>
      }
    >
      <NoteEditorForm
        ref={formRef}
        open={open}
        note={note}
        initialChapterIds={initialChapterIds}
        initialHighlightIds={initialHighlightIds}
        initialBody={initialBody}
        onSaved={onClose}
        onStatusChange={setStatus}
      />
    </CommonDialog>
  );
};
