import type { ChapterPrereadingResponse } from '@/api/generated/model';
import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
} from '@/api/generated/prereading/prereading';
import { AIActionButton } from '@/components/buttons/AIActionButton.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { Box, CircularProgress, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
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
  const [answers, setAnswers] = useState<Record<number, string>>({});

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

  const handleGenerate = () => {
    generate({ chapterId });
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
                  onChange={(e) => setAnswers((prev) => ({ ...prev, [index]: e.target.value }))}
                />
              </Box>
            ))}
          </Stack>
        </CollapsibleSection>
      )}
    </AIFeature>
  );
};
