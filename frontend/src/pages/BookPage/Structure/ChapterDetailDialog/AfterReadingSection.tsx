import { AIActionButton } from '@/components/buttons/AIActionButton.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { Box } from '@mui/material';

interface AfterReadingSectionProps {
  onStartQuiz: () => void;
}

export const AfterReadingSection = ({ onStartQuiz }: AfterReadingSectionProps) => {
  return (
    <AIFeature>
      <Box sx={{ py: 1 }}>
        <AIActionButton text="Quiz me" onClick={onStartQuiz} />
      </Box>
    </AIFeature>
  );
};
