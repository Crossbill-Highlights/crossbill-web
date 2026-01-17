import { Collapsable } from '@/components/animations/Collapsable';
import { HoverableCardActionArea } from '@/components/cards/HoverableCardActionArea';
import { ExpandLessIcon, ExpandMoreIcon } from '@/theme/Icons.tsx';
import { markdownStyles } from '@/theme/theme';
import { Box, Button, styled } from '@mui/material';
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

const ToggleButton = styled(Button)(({ theme }) => ({
  marginTop: theme.spacing(1),
  color: theme.palette.text.secondary,
  fontWeight: 500,
  textTransform: 'none',
  padding: 0,
  minWidth: 'auto',
  '&:hover': {
    backgroundColor: 'transparent',
    color: theme.palette.primary.main,
  },
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
          <>
            <Collapsable isExpanded={isExpanded}>
              <ExpandedContent>
                <ReactMarkdown>{summary}</ReactMarkdown>
              </ExpandedContent>
            </Collapsable>

            <ToggleButton
              size="small"
              endIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            >
              {isExpanded ? 'Show less' : 'Show more'}
            </ToggleButton>
          </>
        )}
      </Box>
    </HoverableCardActionArea>
  );
};
