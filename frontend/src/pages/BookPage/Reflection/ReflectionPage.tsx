import type {
  BookReflectionResponse,
  BookReflectionUpdateRequest,
  Note,
  NoteWithLinks,
} from '@/api/generated/model';
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import {
  getGetBookReflectionApiV1BooksBookIdReflectionGetQueryKey,
  useGetBookReflectionApiV1BooksBookIdReflectionGet,
  useUpsertBookReflectionApiV1BooksBookIdReflectionPut,
} from '@/api/generated/reflections/reflections.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { SectionTitle } from '@/components/typography/SectionTitle.tsx';
import { useBookMutationHelpers } from '@/hooks/useBookMutationHelpers.ts';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { NoteEditorDialog } from '@/pages/BookPage/Notes/NoteEditorDialog.tsx';
import { EditIcon } from '@/theme/Icons.tsx';
import { markdownStyles } from '@/theme/theme';
import { Box, Button, Stack, Typography, useTheme } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { READING_STAGE_HINTS, type ReadingStageValue } from './readingStages.ts';
import { ReflectionNotesSection } from './ReflectionNotesSection.tsx';
import {
  REFLECTION_QUESTIONS,
  emptyReflection,
  type ReflectionQuestion,
} from './reflectionQuestions.ts';

interface EditorState {
  question: ReflectionQuestion;
  note: NoteWithLinks | null;
}

export const ReflectionPage = () => {
  const { book } = useBookPage();
  const bookId = book.id;
  const theme = useTheme();
  const queryClient = useQueryClient();
  const { mutationErrorHandler } = useBookMutationHelpers(bookId);

  const queryKey = getGetBookReflectionApiV1BooksBookIdReflectionGetQueryKey(bookId);
  const { data: reflection, isLoading } = useGetBookReflectionApiV1BooksBookIdReflectionGet(bookId);
  const { data: notesData } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId);
  const allNotes = notesData?.items ?? [];
  const notesById = new Map(allNotes.map((note) => [note.id, note]));

  const [editor, setEditor] = useState<EditorState | null>(null);

  const server = reflection ?? emptyReflection(bookId);

  const { mutate: save } = useUpsertBookReflectionApiV1BooksBookIdReflectionPut({
    mutation: {
      onSuccess: (updated) => {
        queryClient.setQueryData<BookReflectionResponse>(queryKey, updated);
      },
      onError: mutationErrorHandler('save reflection'),
    },
  });

  const persist = (overrides: Partial<BookReflectionUpdateRequest>) => {
    save({
      bookId,
      data: {
        what_is_it_about_note_id: server.what_is_it_about_note_id ?? null,
        what_does_it_say_note_id: server.what_does_it_say_note_id ?? null,
        do_i_agree_note_id: server.do_i_agree_note_id ?? null,
        so_what_note_id: server.so_what_note_id ?? null,
        note_ids: server.note_ids ?? [],
        ...overrides,
      },
    });
  };

  const handleCreated = (question: ReflectionQuestion, note: Note) => {
    persist({ [question.noteIdField]: note.id });
  };

  const handleNoteIdsChange = (noteIds: number[]) => {
    persist({ note_ids: noteIds });
  };

  if (isLoading) return <Spinner />;

  const stageHint = book.reading_stage
    ? READING_STAGE_HINTS[book.reading_stage as ReadingStageValue]
    : undefined;

  return (
    <Box sx={{ maxWidth: 760, mx: 'auto', py: 1 }}>
      {stageHint && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
          {stageHint}
        </Typography>
      )}

      <Stack gap={4}>
        {REFLECTION_QUESTIONS.map((question) => {
          const noteId = server[question.noteIdField];
          const answerNote = noteId != null ? notesById.get(noteId) : undefined;

          return (
            <Box key={question.noteIdField}>
              <SectionTitle>{question.title}</SectionTitle>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                {question.guide}
              </Typography>

              {noteId != null && !answerNote && <Spinner size={24} />}

              {answerNote && (
                <Box
                  sx={{
                    bgcolor: 'action.hover',
                    borderRadius: 1,
                    px: 2,
                    py: 1.5,
                    position: 'relative',
                  }}
                >
                  <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
                    <IconButtonWithTooltip
                      title="Edit answer"
                      icon={<EditIcon fontSize="small" />}
                      onClick={() => setEditor({ question, note: answerNote })}
                    />
                  </Box>
                  <Box sx={{ ...markdownStyles(theme), pr: 4 }}>
                    <ReactMarkdown>{answerNote.body}</ReactMarkdown>
                  </Box>
                </Box>
              )}

              {noteId == null && (
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setEditor({ question, note: null })}
                >
                  Answer
                </Button>
              )}

              {question.noteIdField === 'what_does_it_say_note_id' && (
                <Box sx={{ mt: 2 }}>
                  <ReflectionNotesSection
                    bookId={bookId}
                    noteIds={server.note_ids ?? []}
                    allNotes={allNotes}
                    onChange={handleNoteIdsChange}
                  />
                </Box>
              )}
            </Box>
          );
        })}
      </Stack>

      {editor && (
        <NoteEditorDialog
          open
          onClose={() => setEditor(null)}
          note={editor.note}
          initialKind={editor.note ? undefined : 'reflection'}
          initialTitle={editor.note ? undefined : editor.question.title}
          guidance={{ title: editor.question.title, text: editor.question.guide }}
          onCreated={(note) => handleCreated(editor.question, note)}
        />
      )}
    </Box>
  );
};
