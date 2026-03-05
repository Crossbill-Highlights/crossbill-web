import { AIIcon } from '@/theme/Icons';
import { Button } from '@mui/material';

export const AIActionButton = ({
  text,
  onClick,
  disabled = false,
}: {
  text: string;
  onClick: () => void;
  disabled?: boolean;
}) => (
  <Button
    variant="text"
    size="small"
    startIcon={<AIIcon />}
    onClick={onClick}
    disabled={disabled}
    sx={{ mb: 1 }}
  >
    {text}
  </Button>
);
