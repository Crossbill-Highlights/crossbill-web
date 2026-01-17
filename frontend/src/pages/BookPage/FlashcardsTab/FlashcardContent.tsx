import { Collapsable } from '@/components/animations/Collapsable.tsx';
import { QuoteIcon } from '@/theme/Icons.tsx';
import { Box, Typography } from '@mui/material';

export interface FlashcardContentProps {
  question: string;
  answer: string;
  isExpanded: boolean;
  showSourceHighlight?: boolean;
  sourceHighlightText?: string;
}

export const FlashcardContent = ({
  question,
  answer,
  isExpanded,
  showSourceHighlight = false,
  sourceHighlightText,
}: FlashcardContentProps) => {
  return (
    <>
      {/* Question */}
      <Box
        sx={{
          mb: isExpanded ? 2 : 1,
          pr: 6,
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: 'primary.main',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            display: 'block',
            mb: 0.5,
          }}
        >
          Question
        </Typography>
        <Typography variant="body1" sx={{ lineHeight: 1.5 }}>
          {question}
        </Typography>
      </Box>

      <Collapsable isExpanded={isExpanded}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
          <Typography
            variant="caption"
            sx={{
              color: 'secondary.main',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Answer
          </Typography>
        </Box>

        <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.5 }}>
          {answer}
        </Typography>

        {/* Source highlight preview */}
        {showSourceHighlight && sourceHighlightText && (
          <Box
            sx={{
              mt: 2,
              pt: 2,
              borderTop: '1px dashed',
              borderColor: 'divider',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
              <QuoteIcon sx={{ fontSize: 14, color: 'text.disabled', mt: 0.25, flexShrink: 0 }} />
              <Typography
                variant="caption"
                sx={{
                  color: 'text.disabled',
                  fontStyle: 'italic',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  lineHeight: 1.4,
                }}
              >
                {sourceHighlightText}
              </Typography>
            </Box>
          </Box>
        )}
      </Collapsable>
    </>
  );
};
