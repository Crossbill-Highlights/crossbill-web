import type { ChapterWithHighlights, PositionResponse } from '@/api/generated/model';
import { ExpandMoreIcon, FlashcardsIcon, HighlightsIcon } from '@/theme/Icons.tsx';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  ButtonBase,
  Typography,
} from '@mui/material';
import { sumBy } from 'lodash';
import type { ReactNode } from 'react';
import { useState } from 'react';

interface ChapterAccordionProps {
  chapter: ChapterWithHighlights;
  childrenByParentId: Map<number | null, ChapterWithHighlights[]>;
  bookId: number;
  depth?: number;
  isRead?: boolean;
  readingPosition?: PositionResponse | null;
  preExpanded?: boolean;
  onChapterClick?: (chapterId: number) => void;
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
  chapter,
  depth,
  onClick,
}: {
  chapter: ChapterWithHighlights;
  depth: number;
  onClick?: () => void;
}) => {
  const highlightCount = chapter.highlights.length;
  const flashcardCount = sumBy(chapter.highlights, (h) => h.flashcards.length);

  return (
    <ButtonBase
      onClick={onClick}
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
        width: '100%',
        textAlign: 'left',
        transition: 'background-color 0.2s ease',
        '@media (hover: hover)': {
          '&:hover': {
            bgcolor: 'action.hover',
          },
        },
        '&:last-of-type': {
          borderBottom: depth > 0 ? 'none' : '1px solid',
          borderColor: 'divider',
        },
      })}
    >
      <Typography variant="body1" sx={{ fontWeight: 600 }}>
        {chapter.name}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, color: 'text.secondary' }}>
        {highlightCount > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <HighlightsIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption">{highlightCount}</Typography>
          </Box>
        )}
        {flashcardCount > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <FlashcardsIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption">{flashcardCount}</Typography>
          </Box>
        )}
      </Box>
    </ButtonBase>
  );
};

export const ChapterAccordion = ({
  chapter,
  childrenByParentId,
  bookId,
  depth = 0,
  isRead,
  readingPosition,
  preExpanded = false,
  onChapterClick,
}: ChapterAccordionProps) => {
  const [expanded, setExpanded] = useState(preExpanded);

  const childChapters = childrenByParentId.get(chapter.id) ?? [];
  const isLeaf = childChapters.length === 0;

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
              depth={depth + 1}
              isRead={
                readingPosition != null && child.start_position != null
                  ? readingPosition.index >= child.start_position.index
                  : undefined
              }
              readingPosition={readingPosition}
              onChapterClick={onChapterClick}
            />
          ))}
        </Box>
      </ExpandableChapter>
    );
  } else {
    content = (
      <LeafChapterRow
        chapter={chapter}
        depth={depth}
        onClick={() => onChapterClick?.(chapter.id)}
      />
    );
  }

  return <Box data-chapter-read={isRead ? 'true' : 'false'}>{content}</Box>;
};
