import type { ChapterWithHighlights } from '@/api/generated/model';
import {
  getGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
  useGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGet,
} from '@/api/generated/prereading/prereading';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { ExpandMoreIcon } from '@/theme/Icons.tsx';
import { Accordion, AccordionDetails, AccordionSummary, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { PrereadingContent } from './PrereadingContent';

interface ChapterAccordionProps {
  chapter: ChapterWithHighlights;
}

export const ChapterAccordion = ({ chapter }: ChapterAccordionProps) => {
  const [expanded, setExpanded] = useState(false);
  const queryClient = useQueryClient();

  const { data: prereading } = useGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGet(
    chapter.id,
    { query: { enabled: expanded } }
  );

  const { mutate: generate, isPending } =
    useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost({
      mutation: {
        onSuccess: () => {
          void queryClient.invalidateQueries({
            queryKey: getGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGetQueryKey(
              chapter.id
            ),
          });
        },
      },
    });

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{
        boxShadow: 'none',
        '&:before': { display: 'none' },
        bgcolor: 'background.paper',
      }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="body1">{chapter.name}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <AIFeature>
          <PrereadingContent
            content={prereading}
            onGenerate={() => generate({ chapterId: chapter.id })}
            isGenerating={isPending}
          />
        </AIFeature>
      </AccordionDetails>
    </Accordion>
  );
};
