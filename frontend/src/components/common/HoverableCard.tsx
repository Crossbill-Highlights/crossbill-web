import { Card, CardProps } from '@mui/material';
import { SxProps, Theme } from '@mui/material/styles';

export type HoverEffect = 'lift' | 'borderGlow' | 'both';

export interface HoverableCardProps extends Omit<CardProps, 'sx'> {
  hoverEffect?: HoverEffect;
  sx?: SxProps<Theme>;
}

export const HoverableCard = ({
  hoverEffect = 'both',
  sx,
  children,
  ...rest
}: HoverableCardProps) => {
  return (
    <Card
      sx={{
        transition: 'all 0.2s',
        cursor: 'pointer',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 3,
        },
        ...sx,
      }}
      {...rest}
    >
      {children}
    </Card>
  );
};
