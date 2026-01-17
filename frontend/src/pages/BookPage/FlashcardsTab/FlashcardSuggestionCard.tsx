import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip';
import { FlashcardCard } from '@/pages/BookPage/FlashcardsTab/FlashcardCard.tsx';
import { Check as AcceptIcon, Close as RejectIcon } from '@mui/icons-material';

export interface FlashcardSuggestionCardProps {
  question: string;
  answer: string;
  onAccept: () => void;
  onReject: () => void;
}

export const FlashcardSuggestionCard = ({
  question,
  answer,
  onAccept,
  onReject,
}: FlashcardSuggestionCardProps) => {
  const handleAccept = (e: React.MouseEvent) => {
    e.stopPropagation();
    onAccept();
  };

  const handleReject = (e: React.MouseEvent) => {
    e.stopPropagation();
    onReject();
  };

  return (
    <FlashcardCard
      question={question}
      answer={answer}
      borderStyle="dashed"
      renderActions={() => (
        <>
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
        </>
      )}
    />
  );
};
