import { ExpandLessIcon, ExpandMoreIcon } from '@/components/common/Icons';
import { Collapsable } from '@/components/common/animations/Collapsable';
import { markdownStyles } from '@/theme/theme';
import { Box, Button, CardActionArea, styled } from '@mui/material';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface AISummaryProps {
  summary?: string | null;
}

const SummaryCard = styled(CardActionArea)(({ theme }) => ({
  padding: theme.spacing(1.5, 2),
  borderRadius: theme.spacing(0.75),
  borderLeft: `3px solid transparent`,
  transition: 'all 0.2s ease',
  cursor: 'pointer',
  '@media (hover: hover)': {
    '&:hover': {
      backgroundColor: theme.palette.action.hover,
      borderLeftColor: theme.palette.primary.main,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
    },
  },
}));

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
    <SummaryCard onClick={() => setIsExpanded(!isExpanded)}>
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
    </SummaryCard>
  );
};
