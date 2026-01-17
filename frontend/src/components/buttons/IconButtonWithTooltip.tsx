import { IconButton, Tooltip } from '@mui/material';
import type { ReactNode } from 'react';

interface IconButtonWithTooltipProps {
  title: string;
  onClick: (e: React.MouseEvent) => void;
  disabled?: boolean;
  ariaLabel?: string;
  icon: ReactNode;
}

export const IconButtonWithTooltip = ({
  title,
  onClick,
  disabled,
  ariaLabel,
  icon,
}: IconButtonWithTooltipProps) => {
  return (
    <Tooltip title={title}>
      <IconButton onClick={onClick} disabled={disabled} aria-label={ariaLabel} size="small">
        {icon}
      </IconButton>
    </Tooltip>
  );
};
