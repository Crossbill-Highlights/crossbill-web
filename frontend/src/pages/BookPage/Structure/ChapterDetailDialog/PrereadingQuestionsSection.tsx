import type { ChapterPrereadingResponse } from '@/api/generated/model';
import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
  useUpdatePrereadingAnswersApiV1ChaptersChapterIdPrereadingAnswersPut,
} from '@/api/generated/prereading/prereading';
import { AIActionButton } from '@/components/buttons/AIActionButton.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { Box, CircularProgress, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface PrereadingQuestionsSectionProps {
  chapterId: number;
  bookId: number;
  prereadingSummary?: ChapterPrereadingResponse;
}

export const PrereadingQuestionsSection = ({
  chapterId,
  bookId,
  prereadingSummary,
}: PrereadingQuestionsSectionProps) => {
  const queryClient = useQueryClient();

  // Local edits keyed by chapterId so they reset when switching chapters
  const [localEdits, setLocalEdits] = useState<Record<number, Record<number, string>>>({});
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Server answers derived from prereadingSummary
  const serverAnswers = useMemo<Record<number, string>>(() => {
    if (!prereadingSummary) return {};
    return Object.fromEntries(
      prereadingSummary.questions.map((q, index) => [index, q.user_answer])
    );
  }, [prereadingSummary]);

  // Merge server answers with local edits for the current chapter
  const answers: Record<number, string> = {
    ...serverAnswers,
    ...(localEdits[chapterId] ?? {}),
  };

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current !== null) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const { mutate: generate, isPending } =
    useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost({
      mutation: {
        onSuccess: () => {
          void queryClient.invalidateQueries({
            queryKey: getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey(bookId),
          });
        },
      },
    });

  const { mutate: saveAnswers } =
    useUpdatePrereadingAnswersApiV1ChaptersChapterIdPrereadingAnswersPut();

  const debouncedSave = useCallback(
    (updatedAnswers: Record<number, string>) => {
      if (debounceTimerRef.current !== null) {
        clearTimeout(debounceTimerRef.current);
      }
      debounceTimerRef.current = setTimeout(() => {
        const answerList = Object.entries(updatedAnswers).map(([index, answer]) => ({
          question_index: Number(index),
          user_answer: answer,
        }));
        saveAnswers({
          chapterId,
          data: { answers: answerList },
        });
      }, 1000);
    },
    [chapterId, saveAnswers]
  );

  const handleGenerate = () => {
    generate({ chapterId });
  };

  const handleAnswerChange = (index: number, value: string) => {
    const updatedChapterEdits = { ...(localEdits[chapterId] ?? {}), [index]: value };
    setLocalEdits((prev) => ({ ...prev, [chapterId]: updatedChapterEdits }));
    const updatedAnswers = { ...serverAnswers, ...updatedChapterEdits };
    debouncedSave(updatedAnswers);
  };

  return (
    <AIFeature>
      {isPending && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {!isPending && !prereadingSummary && (
        <Box sx={{ py: 1 }}>
          <AIActionButton text="Generate questions" onClick={handleGenerate} />
        </Box>
      )}

      {!isPending && prereadingSummary && prereadingSummary.questions.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          No pre-reading questions available.
        </Typography>
      )}

      {!isPending && prereadingSummary && prereadingSummary.questions.length > 0 && (
        <CollapsibleSection title="Questions to think while reading" defaultExpanded>
          <Stack gap={1}>
            {prereadingSummary.questions.map((q, index) => (
              <Box key={index} sx={{ py: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1.5 }}>
                  {q.question}
                </Typography>
                <TextField
                  multiline
                  minRows={2}
                  fullWidth
                  size="small"
                  placeholder="Write your answer..."
                  value={answers[index] ?? ''}
                  onChange={(e) => handleAnswerChange(index, e.target.value)}
                />
              </Box>
            ))}
          </Stack>
        </CollapsibleSection>
      )}
    </AIFeature>
  );
};
