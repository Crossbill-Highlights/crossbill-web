import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip';
import { FlashcardContent } from '@/pages/BookPage/FlashcardsTab/FlashcardContent.tsx';
import { Check as AcceptIcon, Close as RejectIcon } from '@mui/icons-material';
import { Box, Card, CardActionArea, CardContent, styled } from '@mui/material';
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
          <FlashcardContent question={question} answer={answer} isExpanded={isExpanded} />
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
