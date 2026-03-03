import { Collapsable } from '@/components/animations/Collapsable';
import { HoverableCardActionArea } from '@/components/cards/HoverableCardActionArea';
import { markdownStyles } from '@/theme/theme';
import { Box, styled } from '@mui/material';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface AISummaryProps {
  summary?: string | null;
}

const PreviewContent = styled(Box)(({ theme }) => ({
  display: '-webkit-box',
  WebkitLineClamp: 3,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
  ...markdownStyles(theme),
}));

const ExpandedContent = styled(Box)(({ theme }) => ({
  ...markdownStyles(theme),
}));

export const AISummary = ({ summary }: AISummaryProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!summary) {
    return null;
  }

  return (
    <HoverableCardActionArea
      onClick={() => setIsExpanded(!isExpanded)}
      sx={(theme) => ({ padding: theme.spacing(1.5, 2) })}
    >
      <Box sx={{ pointerEvents: 'none' }}>
        {!isExpanded && summary && (
          <PreviewContent>
            <ReactMarkdown>{summary}</ReactMarkdown>
          </PreviewContent>
        )}

        {summary && (
          <Collapsable isExpanded={isExpanded}>
            <ExpandedContent>
              <ReactMarkdown>{summary}</ReactMarkdown>
            </ExpandedContent>
          </Collapsable>
        )}
      </Box>
    </HoverableCardActionArea>
  );
};
