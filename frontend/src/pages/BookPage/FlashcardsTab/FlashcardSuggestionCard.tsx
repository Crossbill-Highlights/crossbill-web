import { Collapsable } from '@/components/animations/Collapsable.tsx';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip';
import { Check as AcceptIcon, Close as RejectIcon } from '@mui/icons-material';
import { Box, Card, CardActionArea, CardContent, styled, Typography } from '@mui/material';
import { useState } from 'react';

export interface FlashcardSuggestionCardProps {
  question: string;
  answer: string;
  onAccept: () => void;
  onReject: () => void;
}

const FlashcardSuggestionStyled = styled(Card)(({ theme }) => ({
  height: 'fit-content',
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  transition: 'all 0.2s ease',
  bgcolor: 'background.paper',
  border: `1px dashed ${theme.palette.divider}`,
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: 3,
  },
}));

const ActionButtonsStyled = styled(Box)(() => ({
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

export const FlashcardSuggestionCard = ({
  question,
  answer,
  onAccept,
  onReject,
}: FlashcardSuggestionCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleAccept = (e: React.MouseEvent) => {
    e.stopPropagation();
    onAccept();
  };

  const handleReject = (e: React.MouseEvent) => {
    e.stopPropagation();
    onReject();
  };

  return (
    <FlashcardSuggestionStyled>
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
          </Collapsable>
        </CardContent>
      </CardActionArea>

      <ActionButtonsStyled>
        <IconButtonWithTooltip
          title="Accept"
          ariaLabel="Accept suggestion"
          onClick={handleAccept}
          icon={<AcceptIcon fontSize="small" />}
        />
        <IconButtonWithTooltip
          title="Reject"
          ariaLabel="Reject suggestion"
          onClick={handleReject}
          icon={<RejectIcon fontSize="small" />}
        />
      </ActionButtonsStyled>
    </FlashcardSuggestionStyled>
  );
};
