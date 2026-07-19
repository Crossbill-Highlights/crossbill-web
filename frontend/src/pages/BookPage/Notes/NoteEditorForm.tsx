import type { NoteWithLinks, TagInBook } from '@/api/generated/model';
import {
  getGetNoteApiV1NotesNoteIdGetQueryKey,
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useCreateNoteApiV1NotesPost,
  useUpdateNoteApiV1NotesNoteIdPut,
} from '@/api/generated/notes/notes.ts';
import { TagInput } from '@/components/inputs/TagInput.tsx';
import { useBookMutationHelpers } from '@/hooks/useBookMutationHelpers.ts';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { Autocomplete, Box, MenuItem, TextField } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { forwardRef, useEffect, useImperativeHandle } from 'react';
import { Controller, useForm } from 'react-hook-form';

import { useNoteTagField } from './hooks/useNoteTagField';
import { NOTE_KIND_LABELS, NOTE_KINDS, type NoteKindValue } from './noteKinds';

export interface NoteEditorFormHandle {
  submit: () => void;
}

interface NoteEditorFormProps {
  /** Drives the reset effect: form values are (re)initialised when this flips true. */
  open: boolean;
  /** Edit mode when set; create mode otherwise */
  note?: NoteWithLinks | null;
  initialChapterIds?: number[];
  initialHighlightIds?: number[];
  initialBody?: string;
  /** Called after a successful create/update. */
  onSaved: () => void;
  /** Reports save-ability so the hosting dialog can render its footer buttons. */
  onStatusChange?: (status: { isSaving: boolean; canSave: boolean }) => void;
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
  tags: TagInBook[];
}

const EMPTY_FORM: NoteFormValues = { title: '', body: '', kind: '', chapters: [], tags: [] };

/**
 * The note create/edit form fields plus mutations, without a dialog shell.
 * Shared by `NoteEditorDialog` (create + standalone edit) and `NoteViewModal`'s
 * in-place edit mode. The host renders the footer buttons and triggers save via
 * the imperative `submit` handle.
 */
export const NoteEditorForm = forwardRef<NoteEditorFormHandle, NoteEditorFormProps>(
  function NoteEditorForm(
    { open, note, initialChapterIds, initialHighlightIds, initialBody, onSaved, onStatusChange },
    ref
  ) {
    const { book } = useBookPage();
    const { mutationErrorHandler } = useBookMutationHelpers(book.id);
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
          tags: book.tags.filter((tag) => note.tag_ids.includes(tag.id)),
        });
      } else {
        reset({
          ...EMPTY_FORM,
          body: initialBody ?? '',
          chapters: chapterOptions.filter((option) =>
            (initialChapterIds ?? []).includes(option.id)
          ),
        });
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open, note]);

    const invalidateNotes = () => {
      void queryClient.invalidateQueries({
        queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(book.id),
      });
      // Refresh the single-note detail so the view dialog reflects edits immediately.
      if (note) {
        void queryClient.invalidateQueries({
          queryKey: getGetNoteApiV1NotesNoteIdGetQueryKey(note.id),
        });
      }
    };

    const { resolveTags, isCreating: isCreatingTag } = useNoteTagField(book.id);

    const createMutation = useCreateNoteApiV1NotesPost({
      mutation: {
        onSuccess: () => {
          invalidateNotes();
          onSaved();
        },
        onError: mutationErrorHandler('create note'),
      },
    });
    const updateMutation = useUpdateNoteApiV1NotesNoteIdPut({
      mutation: {
        onSuccess: () => {
          invalidateNotes();
          onSaved();
        },
        onError: mutationErrorHandler('update note'),
      },
    });

    const isSaving = createMutation.isPending || updateMutation.isPending;
    const canSave = watch('title').trim().length > 0 && !isSaving;

    useEffect(() => {
      onStatusChange?.({ isSaving, canSave });
    }, [isSaving, canSave, onStatusChange]);

    const onSubmit = async (values: NoteFormValues) => {
      const payload = {
        title: values.title.trim(),
        body: values.body,
        kind: values.kind === '' ? null : values.kind,
        chapter_ids: values.chapters.map((option) => option.id),
        highlight_ids: note?.highlight_ids ?? initialHighlightIds ?? [],
        tag_ids: values.tags.map((tag) => tag.id),
      };
      if (note) {
        await updateMutation.mutateAsync({ noteId: note.id, data: payload });
      } else {
        await createMutation.mutateAsync({ data: { ...payload, book_id: book.id } });
      }
    };

    useImperativeHandle(ref, () => ({
      submit: () => void handleSubmit(onSubmit)(),
    }));

    return (
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
            <TagInput
              value={field.value}
              onChange={(newValue) => resolveTags(newValue, book.tags).then(field.onChange)}
              availableTags={book.tags}
              isProcessing={isCreatingTag}
            />
          )}
        />
      </Box>
    );
  }
);
