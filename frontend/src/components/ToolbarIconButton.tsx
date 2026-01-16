import { IconButton, Tooltip } from '@mui/material';
import type { ReactNode } from 'react';

interface ToolbarIconButtonProps {
  title: string;
  onClick: () => void;
  disabled: boolean;
  ariaLabel: string;
  icon: ReactNode;
}

export const ToolbarIconButton = ({
  title,
  onClick,
  disabled,
  ariaLabel,
  icon,
}: ToolbarIconButtonProps) => {
  return (
    <Tooltip title={title}>
      <IconButton onClick={onClick} disabled={disabled} aria-label={ariaLabel} size="small">
        {icon}
      </IconButton>
    </Tooltip>
  );
};
