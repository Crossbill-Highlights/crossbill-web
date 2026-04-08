import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
} from '@/api/generated/prereading/prereading';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { AIIcon, RegenerateIcon } from '@/theme/Icons.tsx';
import { Box, CircularProgress } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';

interface ChapterToolbarProps {
  chapterId: number;
  bookId: string;
  hasSummary: boolean;
}

export const ChapterToolbar = ({ chapterId, bookId, hasSummary }: ChapterToolbarProps) => {
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

  const title = hasSummary ? 'Regenerate summary and questions' : 'Generate summary';
  const icon = hasSummary ? <RegenerateIcon /> : <AIIcon />;

  return (
    <AIFeature>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
        {isPending ? (
          <CircularProgress size={24} sx={{ m: '4px' }} />
        ) : (
          <IconButtonWithTooltip
            title={title}
            onClick={handleGenerate}
            ariaLabel={title}
            icon={icon}
          />
        )}
      </Box>
    </AIFeature>
  );
};
