import type { BookReflectionResponse, BookReflectionUpdateRequest } from '@/api/generated/model';
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import {
  getGetBookReflectionApiV1BooksBookIdReflectionGetQueryKey,
  useGetBookReflectionApiV1BooksBookIdReflectionGet,
  useUpsertBookReflectionApiV1BooksBookIdReflectionPut,
} from '@/api/generated/reflections/reflections.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { SectionTitle } from '@/components/typography/SectionTitle.tsx';
import { useBookMutationHelpers } from '@/hooks/useBookMutationHelpers.ts';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { Box, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { ChapterGistsContext } from './ChapterGistsContext.tsx';
import { READING_STAGE_HINTS, type ReadingStageValue } from './readingStages.ts';
import { ReflectionNotesSection } from './ReflectionNotesSection.tsx';
import {
  REFLECTION_QUESTIONS,
  emptyReflection,
  type ReflectionField,
} from './reflectionQuestions.ts';

export const ReflectionPage = () => {
  const { book } = useBookPage();
  const bookId = book.id;
  const queryClient = useQueryClient();
  const { mutationErrorHandler } = useBookMutationHelpers(bookId);

  const queryKey = getGetBookReflectionApiV1BooksBookIdReflectionGetQueryKey(bookId);
  const { data: reflection, isLoading } = useGetBookReflectionApiV1BooksBookIdReflectionGet(bookId);
  const { data: notesData } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId);
  const allNotes = notesData?.items ?? [];

  const [localEdits, setLocalEdits] = useState<Partial<Record<ReflectionField, string>>>({});

  const server = reflection ?? emptyReflection(bookId);

  const answers: Record<ReflectionField, string> = {
    what_is_it_about: server.what_is_it_about,
    what_does_it_say: server.what_does_it_say,
    do_i_agree: server.do_i_agree,
    so_what: server.so_what,
    ...localEdits,
  };

  const { mutate: save } = useUpsertBookReflectionApiV1BooksBookIdReflectionPut({
    mutation: {
      onSuccess: (updated) => {
        queryClient.setQueryData<BookReflectionResponse>(queryKey, updated);
        setLocalEdits({});
      },
      onError: mutationErrorHandler('save reflection'),
    },
  });

  const persist = (overrides: Partial<BookReflectionUpdateRequest>) => {
    save({
      bookId,
      data: {
        what_is_it_about: answers.what_is_it_about,
        what_does_it_say: answers.what_does_it_say,
        do_i_agree: answers.do_i_agree,
        so_what: answers.so_what,
        note_ids: server.note_ids ?? [],
        ...overrides,
      },
    });
  };

  const handleChange = (field: ReflectionField, value: string) => {
    setLocalEdits((prev) => ({ ...prev, [field]: value }));
  };

  const handleBlur = () => {
    persist({});
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

      <Box sx={{ mb: 3 }}>
        <ChapterGistsContext bookId={bookId} />
      </Box>

      <Stack gap={4}>
        {REFLECTION_QUESTIONS.map((question) => (
          <Box key={question.field}>
            <SectionTitle>{question.title}</SectionTitle>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {question.guide}
            </Typography>
            <TextField
              multiline
              minRows={4}
              fullWidth
              value={answers[question.field]}
              onChange={(event) => handleChange(question.field, event.target.value)}
              onBlur={handleBlur}
            />
            {question.field === 'what_does_it_say' && (
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
        ))}
      </Stack>
    </Box>
  );
};
