import type { HighlightTagInBook, NoteWithLinks } from '@/api/generated/model';
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useCreateNoteApiV1NotesPost,
  useUpdateNoteApiV1NotesNoteIdPut,
} from '@/api/generated/notes/notes.ts';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { HighlightTagInput } from '@/pages/BookPage/Highlights/HighlightViewModal/components/HighlightTagInput.tsx';
import { Autocomplete, Box, Button, MenuItem, TextField } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';

import { useNoteTagField } from './hooks/useNoteTagField';
import { NOTE_KIND_LABELS, NOTE_KINDS, type NoteKindValue } from './noteKinds';

interface NoteEditorDialogProps {
  open: boolean;
  onClose: () => void;
  /** Edit mode when set; create mode otherwise */
  note?: NoteWithLinks | null;
  initialChapterIds?: number[];
  initialHighlightIds?: number[];
  initialBody?: string;
}

interface ChapterOption {
  id: number;
  name: string;
}

interface NoteFormValues {
  title: string;
  body: string;
  kind: NoteKindValue | '';
  chapters: ChapterOption[];
  tags: HighlightTagInBook[];
}

const EMPTY_FORM: NoteFormValues = { title: '', body: '', kind: '', chapters: [], tags: [] };

export const NoteEditorDialog = ({
  open,
  onClose,
  note,
  initialChapterIds,
  initialHighlightIds,
  initialBody,
}: NoteEditorDialogProps) => {
  const { book } = useBookPage();
  const { showSnackbar } = useSnackbar();
  const queryClient = useQueryClient();

  const chapterOptions: ChapterOption[] = book.chapters.map((chapter) => ({
    id: chapter.id,
    name: chapter.name,
  }));

  const { control, handleSubmit, reset, watch } = useForm<NoteFormValues>({
    defaultValues: EMPTY_FORM,
  });

  useEffect(() => {
    if (!open) return;
    if (note) {
      reset({
        title: note.title,
        body: note.body,
        kind: (note.kind as NoteKindValue | null) ?? '',
        chapters: chapterOptions.filter((option) => note.chapter_ids.includes(option.id)),
        tags: book.highlight_tags.filter((tag) => note.highlight_tag_ids.includes(tag.id)),
      });
    } else {
      reset({
        ...EMPTY_FORM,
        body: initialBody ?? '',
        chapters: chapterOptions.filter((option) => (initialChapterIds ?? []).includes(option.id)),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, note]);

  const invalidateNotes = () => {
    void queryClient.invalidateQueries({
      queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(book.id),
    });
  };

  const { resolveTags, isCreating: isCreatingTag } = useNoteTagField(book.id);

  const createMutation = useCreateNoteApiV1NotesPost({
    mutation: {
      onSuccess: () => {
        invalidateNotes();
        onClose();
      },
      onError: (error) => {
        console.error('Failed to create note:', error);
        showSnackbar('Failed to create note. Please try again.', 'error');
      },
    },
  });
  const updateMutation = useUpdateNoteApiV1NotesNoteIdPut({
    mutation: {
      onSuccess: () => {
        invalidateNotes();
        onClose();
      },
      onError: (error) => {
        console.error('Failed to update note:', error);
        showSnackbar('Failed to update note. Please try again.', 'error');
      },
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const canSave = watch('title').trim().length > 0 && !isSaving;

  const onSubmit = async (values: NoteFormValues) => {
    const payload = {
      title: values.title.trim(),
      body: values.body,
      kind: values.kind === '' ? null : values.kind,
      chapter_ids: values.chapters.map((option) => option.id),
      highlight_ids: note?.highlight_ids ?? initialHighlightIds ?? [],
      highlight_tag_ids: values.tags.map((tag) => tag.id),
    };
    if (note) {
      await updateMutation.mutateAsync({ noteId: note.id, data: payload });
    } else {
      await createMutation.mutateAsync({ data: { ...payload, book_id: book.id } });
    }
  };

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      title={note ? 'Edit Note' : 'New Note'}
      maxWidth="md"
      isLoading={isSaving}
      footerActions={
        <Box sx={{ display: 'flex', gap: 1, width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSubmit(onSubmit)} disabled={!canSave}>
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </Box>
      }
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Controller
          name="title"
          control={control}
          render={({ field }) => <TextField {...field} label="Title" fullWidth autoFocus />}
        />
        <Controller
          name="kind"
          control={control}
          render={({ field }) => (
            <TextField {...field} select label="Kind" fullWidth>
              <MenuItem value="">None</MenuItem>
              {NOTE_KINDS.map((value) => (
                <MenuItem key={value} value={value}>
                  {NOTE_KIND_LABELS[value]}
                </MenuItem>
              ))}
            </TextField>
          )}
        />
        <Controller
          name="body"
          control={control}
          render={({ field }) => (
            <TextField {...field} label="Note (markdown)" fullWidth multiline minRows={5} />
          )}
        />
        <Controller
          name="chapters"
          control={control}
          render={({ field }) => (
            <Autocomplete
              multiple
              options={chapterOptions}
              getOptionLabel={(option) => option.name}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              value={field.value}
              onChange={(_, value) => field.onChange(value)}
              renderInput={(params) => <TextField {...params} label="Chapters" />}
            />
          )}
        />
        <Controller
          name="tags"
          control={control}
          render={({ field }) => (
            <HighlightTagInput
              value={field.value}
              onChange={(newValue) =>
                resolveTags(newValue, book.highlight_tags).then(field.onChange)
              }
              availableTags={book.highlight_tags}
              isProcessing={isCreatingTag}
            />
          )}
        />
      </Box>
    </CommonDialog>
  );
};
