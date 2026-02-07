import type { ChapterWithHighlights } from '@/api/generated/model';
import {
  getGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
  useGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGet,
} from '@/api/generated/prereading/prereading';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { ExpandMoreIcon } from '@/theme/Icons.tsx';
import { Accordion, AccordionDetails, AccordionSummary, Box, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { PrereadingContent } from './PrereadingContent';

interface ChapterAccordionProps {
  chapter: ChapterWithHighlights;
  allChapters: ChapterWithHighlights[];
  depth?: number;
}

export const ChapterAccordion = ({ chapter, allChapters, depth = 0 }: ChapterAccordionProps) => {
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

  const childChapters = allChapters.filter((ch) => ch.parent_id === chapter.id);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{
        boxShadow: 'none',
        '&:before': { display: 'none' },
        bgcolor: 'background.paper',
        ml: depth * 2,
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
        {childChapters.length > 0 && (
          <Box sx={{ mt: 1 }}>
            {childChapters.map((child) => (
              <ChapterAccordion
                key={child.id}
                chapter={child}
                allChapters={allChapters}
                depth={depth + 1}
              />
            ))}
          </Box>
        )}
      </AccordionDetails>
    </Accordion>
  );
};
