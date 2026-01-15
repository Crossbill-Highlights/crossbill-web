import { ExpandLessIcon, ExpandMoreIcon } from '@/components/common/Icons';
import { Collapsable } from '@/components/common/animations/Collapsable';
import { Box, Button, CardActionArea, styled } from '@mui/material';
import type { Theme } from '@mui/material/styles';
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

const markdownStyles = (theme: Theme) => ({
  ...theme.typography.body1,
  color: theme.palette.text.primary,

  '& p': {
    margin: 0,
    marginBottom: '0.5em',
    '&:last-child': {
      marginBottom: 0,
    },
  },
  '& ul, & ol': {
    marginTop: '0.5em',
    marginBottom: '0.5em',
    paddingLeft: '1.5em',
  },
  '& li': {
    marginBottom: '0.25em',
  },
  '& strong': {
    fontWeight: 600,
  },
  '& em': {
    fontStyle: 'italic',
  },
});

const PreviewContent = styled(Box)(({ theme }) => ({
  display: '-webkit-box',
  WebkitLineClamp: 3,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
  ...markdownStyles(theme),
}));

const ExpandedContent = styled(Box)(({ theme }) => ({
  ...markdownStyles(theme),
  '& code': {
    fontFamily: 'monospace',
    backgroundColor: theme.customColors.backgrounds.subtle,
    padding: '0.125em 0.25em',
    borderRadius: '0.25em',
    fontSize: '0.9em',
  },
  '& pre': {
    backgroundColor: theme.customColors.backgrounds.subtle,
    padding: '0.75em',
    borderRadius: '0.5em',
    overflow: 'auto',
    marginTop: '0.5em',
    marginBottom: '0.5em',
  },
  '& pre code': {
    backgroundColor: 'transparent',
    padding: 0,
  },
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
