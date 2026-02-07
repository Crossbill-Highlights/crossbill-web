import type { ChapterWithHighlights } from '@/api/generated/model';
import {
  getGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
  useGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGet,
} from '@/api/generated/prereading/prereading';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { AIIcon, ExpandMoreIcon } from '@/theme/Icons.tsx';
import { Accordion, AccordionDetails, AccordionSummary, Box, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { PrereadingContent } from './PrereadingContent';

interface ChapterAccordionProps {
  chapter: ChapterWithHighlights;
  allChapters: ChapterWithHighlights[];
  depth?: number;
}

const accordionSx = (depth: number) => ({
  boxShadow: 'none',
  '&:before': { display: 'none' },
  bgcolor: 'transparent',
  ml: depth * 2,
  borderBottom: '1px solid',
  borderColor: 'divider',
  '&:last-of-type': {
    borderBottom: depth > 0 ? 'none' : '1px solid',
    borderColor: 'divider',
  },
});

export const ChapterAccordion = ({ chapter, allChapters, depth = 0 }: ChapterAccordionProps) => {
  const [expanded, setExpanded] = useState(false);
  const queryClient = useQueryClient();

  const childChapters = allChapters.filter((ch) => ch.parent_id === chapter.id);
  const isLeaf = childChapters.length === 0;

  const { data: prereading, isFetched } =
    useGetChapterPrereadingApiV1ChaptersChapterIdPrereadingGet(chapter.id, {
      query: { enabled: isLeaf },
    });

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

  const handleGenerate = (e: React.MouseEvent) => {
    e.stopPropagation();
    setExpanded(true);
    generate({ chapterId: chapter.id });
  };

  // Mode A — Parent chapter (has children)
  if (!isLeaf) {
    return (
      <Accordion
        expanded={expanded}
        onChange={() => setExpanded(!expanded)}
        sx={accordionSx(depth)}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            {chapter.name}
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ pt: 0 }}>
          <Box>
            {childChapters.map((child) => (
              <ChapterAccordion
                key={child.id}
                chapter={child}
                allChapters={allChapters}
                depth={depth + 1}
              />
            ))}
          </Box>
        </AccordionDetails>
      </Accordion>
    );
  }

  // Leaf: determine if expandable (has content or currently generating)
  const isExpandableLeaf = !!prereading || isPending;

  // Mode B — Leaf with content or currently generating
  if (isExpandableLeaf) {
    return (
      <Accordion
        expanded={expanded}
        onChange={() => setExpanded(!expanded)}
        sx={accordionSx(depth)}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            {chapter.name}
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ pt: 0 }}>
          <PrereadingContent content={prereading} isGenerating={isPending} />
        </AccordionDetails>
      </Accordion>
    );
  }

  // Mode C — Leaf without content (and not generating): flat row
  return (
    <Box
      sx={{
        ml: depth * 2,
        borderBottom: '1px solid',
        borderColor: 'divider',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: 1,
        px: 2,
        minHeight: 48,
        '&:last-of-type': {
          borderBottom: depth > 0 ? 'none' : '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      <Typography variant="body1" sx={{ fontWeight: 600 }}>
        {chapter.name}
      </Typography>
      {isFetched && (
        <AIFeature>
          <IconButtonWithTooltip
            title="Generate Pre-reading Overview"
            onClick={handleGenerate}
            icon={<AIIcon />}
            ariaLabel="Generate pre-reading overview"
          />
        </AIFeature>
      )}
    </Box>
  );
};
