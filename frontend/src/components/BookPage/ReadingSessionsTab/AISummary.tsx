import { AISummaryIcon, ExpandLessIcon, ExpandMoreIcon } from '@/components/common/Icons';
import { Collapsable } from '@/components/common/animations/Collapsable';
import { Box, Button, Typography, styled } from '@mui/material';
import type { Theme } from '@mui/material/styles';
import type { AxiosError } from 'axios';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface AISummaryProps {
  summary?: string | null;
  error?: unknown;
}

const SummaryCard = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(2),
  padding: theme.spacing(2.5),
  borderRadius: theme.spacing(2),
  border: `1px solid ${theme.palette.divider}`,
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    boxShadow: theme.shadows[2],
    borderColor: theme.palette.primary.light,
  },
}));

const HeaderContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1.25),
  marginBottom: theme.spacing(2),
}));

const StyledAISummaryIcon = styled(AISummaryIcon)(({ theme }) => ({
  fontSize: 20,
  color: theme.palette.primary.main,
}));

const HeaderLabel = styled(Typography)(({ theme }) => ({
  fontWeight: 700,
  color: theme.palette.primary.main,
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  fontSize: '0.75rem',
}));

const ErrorContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginBottom: theme.spacing(1.5),
}));

const ErrorText = styled(Typography)(({ theme }) => ({
  color: theme.palette.error.main,
  fontWeight: 500,
}));

const markdownStyles = (theme: Theme) => ({
  lineHeight: 1.75,
  color: theme.palette.text.primary,
  fontWeight: 300,
  letterSpacing: '0.01em',
  textAlign: 'justify' as const,
  fontSize: '0.875rem',
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
  marginTop: theme.spacing(1.5),
  color: theme.palette.primary.main,
  fontWeight: 600,
  textTransform: 'none',
  fontSize: '0.875rem',
  '&:hover': {
    backgroundColor: theme.customColors.dragDrop.hoverBg,
  },
}));

export const AISummary = ({ summary, error }: AISummaryProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getErrorMessage = (err: unknown): string => {
    const axiosError = err as AxiosError;
    if (axiosError.response?.status === 400) {
      return 'Cannot generate summary - no content available for this session';
    }
    return 'Failed to generate summary. Please try again.';
  };

  const errorMessage = error ? getErrorMessage(error) : null;

  // Don't render anything if there's no summary and no error
  if (!summary && !error) {
    return null;
  }

  // Full card view when summary exists
  return (
    <SummaryCard>
      {/* Header with icon and label */}
      <HeaderContainer>
        <StyledAISummaryIcon />
        <HeaderLabel variant="caption">AI Summary</HeaderLabel>
      </HeaderContainer>

      {/* Error state */}
      {errorMessage && (
        <ErrorContainer>
          <ErrorText variant="caption">{errorMessage}</ErrorText>
        </ErrorContainer>
      )}

      {/* Collapsed preview (first 3 lines) */}
      {!isExpanded && summary && (
        <PreviewContent>
          <ReactMarkdown>{summary}</ReactMarkdown>
        </PreviewContent>
      )}

      {/* Expanded content */}
      {summary && (
        <>
          <Collapsable isExpanded={isExpanded}>
            <ExpandedContent>
              <ReactMarkdown>{summary}</ReactMarkdown>
            </ExpandedContent>
          </Collapsable>

          {/* Toggle button */}
          <ToggleButton
            size="small"
            onClick={() => setIsExpanded(!isExpanded)}
            endIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </ToggleButton>
        </>
      )}
    </SummaryCard>
  );
};
