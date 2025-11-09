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
      sx={(theme) => {
        const baseSx: SxProps<Theme> = {
          transition: 'all 0.2s',
          cursor: 'pointer',
        };

        const hoverSx: Record<string, any> = {};

        if (hoverEffect === 'lift' || hoverEffect === 'both') {
          hoverSx.transform = 'translateY(-4px)';
        }

        if (hoverEffect === 'borderGlow' || hoverEffect === 'both') {
          // Convert hex to rgba for border
          const primaryColor = theme.palette.primary.main;
          const r = parseInt(primaryColor.slice(1, 3), 16);
          const g = parseInt(primaryColor.slice(3, 5), 16);
          const b = parseInt(primaryColor.slice(5, 7), 16);
          hoverSx.borderColor = `rgba(${r}, ${g}, ${b}, 0.3)`;
        }

        // Always increase shadow on hover
        hoverSx.boxShadow = 3;

        return {
          ...baseSx,
          '&:hover': hoverSx,
          ...(typeof sx === 'function' ? sx(theme) : sx),
        };
      }}
      {...rest}
    >
      {children}
    </Card>
  );
};
