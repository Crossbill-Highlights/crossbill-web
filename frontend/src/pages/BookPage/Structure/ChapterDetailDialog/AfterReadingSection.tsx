import { AIActionButton } from '@/components/buttons/AIActionButton.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { Box } from '@mui/material';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface AfterReadingSectionProps {
  onStartQuiz: () => void;
}

export const AfterReadingSection = ({ onStartQuiz }: AfterReadingSectionProps) => {
  return (
    <CollapsibleSection title="After reading" defaultExpanded={true}>
      <AIFeature>
        <Box sx={{ py: 1 }}>
          <AIActionButton text="Quiz me" onClick={onStartQuiz} />
        </Box>
      </AIFeature>
    </CollapsibleSection>
  );
};
