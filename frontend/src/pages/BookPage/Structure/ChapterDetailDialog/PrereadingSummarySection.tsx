import type { ChapterPrereadingResponse } from '@/api/generated/model';
import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
} from '@/api/generated/prereading/prereading';
import { AIActionButton } from '@/components/buttons/AIActionButton.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { PrereadingContent } from '@/pages/BookPage/Structure/PrereadingContent.tsx';
import { Box } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface PrereadingSummarySectionProps {
  chapterId: number;
  bookId: number;
  prereadingSummary?: ChapterPrereadingResponse;
  defaultExpanded: boolean;
}

export const PrereadingSummarySection = ({
  chapterId,
  bookId,
  prereadingSummary,
  defaultExpanded,
}: PrereadingSummarySectionProps) => {
  const queryClient = useQueryClient();

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
    <CollapsibleSection title="Chapter summary" defaultExpanded={defaultExpanded}>
      {prereadingSummary || isPending ? (
        <PrereadingContent content={prereadingSummary} isGenerating={isPending} />
      ) : (
        <AIFeature>
          <Box sx={{ py: 1 }}>
            <AIActionButton text={'Generate summary'} onClick={handleGenerate} />
          </Box>
        </AIFeature>
      )}
    </CollapsibleSection>
  );
};
