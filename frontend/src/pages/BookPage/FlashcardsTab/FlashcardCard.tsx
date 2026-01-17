import { Collapsable } from '@/components/animations/Collapsable';
import { QuoteIcon } from '@/theme/Icons';
import { Box, Card, CardActionArea, CardContent, styled, Typography } from '@mui/material';
import { ReactNode, useState } from 'react';

export interface FlashcardCardProps {
  question: string;
  answer: string;
  showSourceHighlight?: boolean;
  sourceHighlightText?: string;
  renderActions: () => ReactNode;
  borderStyle?: 'solid' | 'dashed';
}

const FlashcardStyled = styled(Card, {
  shouldForwardProp: (prop) => prop !== 'borderStyle',
})<{ borderStyle?: 'solid' | 'dashed' }>(({ theme, borderStyle = 'solid' }) => ({
  height: 'fit-content',
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  transition: 'all 0.2s ease',
  bgcolor: 'background.paper',
  border: `1px ${borderStyle} ${theme.palette.divider}`,
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: 3,
  },
}));

export const ActionButtonsStyled = styled(Box)(() => ({
  position: 'absolute',
  top: 8,
  right: 8,
  display: 'flex',
  gap: 0.5,
  zIndex: 1,
  opacity: 0.7,
  transition: 'opacity 0.2s ease',
  '&:hover': {
    opacity: 1,
  },
}));

export const FlashcardCard = ({
  question,
  answer,
  showSourceHighlight,
  sourceHighlightText,
  renderActions,
  borderStyle = 'solid',
}: FlashcardCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <FlashcardStyled borderStyle={borderStyle}>
      <CardActionArea
        onClick={() => setIsExpanded(!isExpanded)}
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'stretch',
          justifyContent: 'flex-start',
        }}
      >
        <CardContent sx={{ width: '100%', pt: 2 }}>
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
                  <QuoteIcon
                    sx={{ fontSize: 14, color: 'text.disabled', mt: 0.25, flexShrink: 0 }}
                  />
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
        </CardContent>
      </CardActionArea>

      <ActionButtonsStyled>{renderActions()}</ActionButtonsStyled>
    </FlashcardStyled>
  );
};
