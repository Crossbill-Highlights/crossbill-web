import type { NoteWithLinks } from '@/api/generated/model';
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useCreateNoteApiV1NotesPost,
  useUpdateNoteApiV1NotesNoteIdPut,
} from '@/api/generated/notes/notes.ts';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { Autocomplete, Box, Button, MenuItem, TextField } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

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

interface TagOption {
  id: number;
  name: string;
}

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
  const tagOptions: TagOption[] = book.highlight_tags.map((tag) => ({
    id: tag.id,
    name: tag.name,
  }));

  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [kind, setKind] = useState<NoteKindValue | ''>('');
  const [chapters, setChapters] = useState<ChapterOption[]>([]);
  const [tags, setTags] = useState<TagOption[]>([]);
  const [highlightIds, setHighlightIds] = useState<number[]>([]);

  useEffect(() => {
    if (!open) return;
    if (note) {
      setTitle(note.title);
      setBody(note.body);
      setKind((note.kind as NoteKindValue | null) ?? '');
      setChapters(chapterOptions.filter((option) => note.chapter_ids.includes(option.id)));
      setTags(tagOptions.filter((option) => note.highlight_tag_ids.includes(option.id)));
      setHighlightIds(note.highlight_ids);
    } else {
      setTitle('');
      setBody(initialBody ?? '');
      setKind('');
      setChapters(chapterOptions.filter((option) => (initialChapterIds ?? []).includes(option.id)));
      setTags([]);
      setHighlightIds(initialHighlightIds ?? []);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, note]);

  const invalidateNotes = () => {
    void queryClient.invalidateQueries({
      queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(book.id),
    });
  };

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
  const canSave = title.trim().length > 0 && !isSaving;

  const handleSave = async () => {
    const payload = {
      title: title.trim(),
      body,
      kind: kind === '' ? null : kind,
      chapter_ids: chapters.map((option) => option.id),
      highlight_ids: highlightIds,
      highlight_tag_ids: tags.map((option) => option.id),
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
          <Button variant="contained" onClick={() => void handleSave()} disabled={!canSave}>
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </Box>
      }
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <TextField
          label="Title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          fullWidth
          autoFocus
        />
        <TextField
          select
          label="Kind"
          value={kind}
          onChange={(event) => setKind(event.target.value as NoteKindValue | '')}
          fullWidth
        >
          <MenuItem value="">None</MenuItem>
          {NOTE_KINDS.map((value) => (
            <MenuItem key={value} value={value}>
              {NOTE_KIND_LABELS[value]}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label="Note (markdown)"
          value={body}
          onChange={(event) => setBody(event.target.value)}
          fullWidth
          multiline
          minRows={5}
        />
        <Autocomplete
          multiple
          options={chapterOptions}
          getOptionLabel={(option) => option.name}
          isOptionEqualToValue={(option, value) => option.id === value.id}
          value={chapters}
          onChange={(_, value) => setChapters(value)}
          renderInput={(params) => <TextField {...params} label="Chapters" />}
        />
        <Autocomplete
          multiple
          options={tagOptions}
          getOptionLabel={(option) => option.name}
          isOptionEqualToValue={(option, value) => option.id === value.id}
          value={tags}
          onChange={(_, value) => setTags(value)}
          renderInput={(params) => <TextField {...params} label="Tags" />}
        />
      </Box>
    </CommonDialog>
  );
};
