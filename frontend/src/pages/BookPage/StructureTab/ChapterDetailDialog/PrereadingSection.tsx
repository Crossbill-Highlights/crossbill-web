import type { ChapterPrereadingResponse } from '@/api/generated/model';
import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
} from '@/api/generated/prereading/prereading';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { PrereadingContent } from '@/pages/BookPage/StructureTab/PrereadingContent.tsx';
import { AIIcon } from '@/theme/Icons.tsx';
import { Box, Button } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface PrereadingSectionProps {
  chapterId: number;
  bookId: number;
  prereading?: ChapterPrereadingResponse;
  defaultExpanded: boolean;
}

export const PrereadingSection = ({
  chapterId,
  bookId,
  prereading,
  defaultExpanded,
}: PrereadingSectionProps) => {
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
    <CollapsibleSection title="Pre-reading" defaultExpanded={defaultExpanded}>
      {prereading || isPending ? (
        <PrereadingContent content={prereading} isGenerating={isPending} />
      ) : (
        <AIFeature>
          <Box sx={{ py: 1 }}>
            <Button variant="outlined" size="small" startIcon={<AIIcon />} onClick={handleGenerate}>
              Generate Pre-reading Overview
            </Button>
          </Box>
        </AIFeature>
      )}
    </CollapsibleSection>
  );
};
