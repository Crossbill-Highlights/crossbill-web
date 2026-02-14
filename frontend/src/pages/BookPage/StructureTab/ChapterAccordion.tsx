import type {
  ChapterPrereadingResponse,
  ChapterWithHighlights,
  PositionResponse,
} from '@/api/generated/model';
import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
} from '@/api/generated/prereading/prereading';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { AIIcon, ExpandMoreIcon } from '@/theme/Icons.tsx';
import { Accordion, AccordionDetails, AccordionSummary, Box, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { PrereadingContent } from './PrereadingContent';

interface ChapterAccordionProps {
  chapter: ChapterWithHighlights;
  childrenByParentId: Map<number | null, ChapterWithHighlights[]>;
  bookId: number;
  prereadingByChapterId: Record<number, ChapterPrereadingResponse>;
  depth?: number;
  isRead?: boolean;
  readingPosition?: PositionResponse | null;
  preExpanded?: boolean;
}

const accordionSx = (depth: number) => (theme: { spacing: (n: number) => string }) => ({
  boxShadow: 'none',
  '&:before': { display: 'none' },
  '&.Mui-expanded': { m: 0 },
  bgcolor: 'transparent',
  ml: theme.spacing(depth * 2),
  borderBottom: '1px solid',
  borderColor: 'divider',
  '&:last-of-type': {
    borderBottom: depth > 0 ? 'none' : '1px solid',
    borderRadius: 0,
    borderColor: 'divider',
  },
});

const ExpandableChapter = ({
  name,
  depth,
  expanded,
  onToggle,
  children,
}: {
  name: string;
  depth: number;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
}) => (
  <Accordion expanded={expanded} onChange={onToggle} sx={accordionSx(depth)}>
    <AccordionSummary
      expandIcon={<ExpandMoreIcon />}
      sx={{
        borderRadius: 0,
        '&.Mui-expanded': { minHeight: 48 },
        '& .MuiAccordionSummary-content.Mui-expanded': { my: '12px' },
      }}
    >
      <Typography variant="body1" sx={{ fontWeight: 600 }}>
        {name}
      </Typography>
    </AccordionSummary>
    <AccordionDetails sx={{ pt: 0 }}>{children}</AccordionDetails>
  </Accordion>
);

const LeafChapterRow = ({
  name,
  depth,
  onGenerate,
}: {
  name: string;
  depth: number;
  onGenerate: (e: React.MouseEvent) => void;
}) => (
  <Box
    sx={(theme) => ({
      ml: theme.spacing(depth * 2),
      borderBottom: '1px solid',
      borderColor: 'divider',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      py: theme.spacing(1),
      px: theme.spacing(2),
      minHeight: 48,
      '&:last-of-type': {
        borderBottom: depth > 0 ? 'none' : '1px solid',
        borderColor: 'divider',
      },
    })}
  >
    <Typography variant="body1" sx={{ fontWeight: 600 }}>
      {name}
    </Typography>
    <AIFeature>
      <IconButtonWithTooltip
        title="Generate Pre-reading Overview"
        onClick={onGenerate}
        icon={<AIIcon />}
        ariaLabel="Generate pre-reading overview"
      />
    </AIFeature>
  </Box>
);

export const ChapterAccordion = ({
  chapter,
  childrenByParentId,
  bookId,
  prereadingByChapterId,
  depth = 0,
  isRead,
  readingPosition,
  preExpanded = false,
}: ChapterAccordionProps) => {
  const [expanded, setExpanded] = useState(preExpanded);
  const queryClient = useQueryClient();

  const childChapters = childrenByParentId.get(chapter.id) ?? [];
  const isLeaf = childChapters.length === 0;

  const prereading = isLeaf ? prereadingByChapterId[chapter.id] : undefined;

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

  const handleGenerate = (e: React.MouseEvent) => {
    e.stopPropagation();
    setExpanded(true);
    generate({ chapterId: chapter.id });
  };

  let content: ReactNode;
  if (!isLeaf) {
    content = (
      <ExpandableChapter
        name={chapter.name}
        depth={depth}
        expanded={expanded}
        onToggle={() => setExpanded(!expanded)}
      >
        <Box>
          {childChapters.map((child) => (
            <ChapterAccordion
              key={child.id}
              chapter={child}
              childrenByParentId={childrenByParentId}
              bookId={bookId}
              prereadingByChapterId={prereadingByChapterId}
              depth={depth + 1}
              isRead={
                readingPosition != null && child.start_position != null
                  ? readingPosition.index >= child.start_position.index
                  : undefined
              }
              readingPosition={readingPosition}
            />
          ))}
        </Box>
      </ExpandableChapter>
    );
  } else if (prereading || isPending) {
    content = (
      <ExpandableChapter
        name={chapter.name}
        depth={depth}
        expanded={expanded}
        onToggle={() => setExpanded(!expanded)}
      >
        <PrereadingContent content={prereading} isGenerating={isPending} />
      </ExpandableChapter>
    );
  } else {
    content = <LeafChapterRow name={chapter.name} depth={depth} onGenerate={handleGenerate} />;
  }

  return <Box data-chapter-read={isRead ? 'true' : 'false'}>{content}</Box>;
};
