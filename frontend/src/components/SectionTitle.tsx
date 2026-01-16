import { Box, Typography } from '@mui/material';

export interface SectionTitleProps {
  children: React.ReactNode;
  component?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
  showDivider?: boolean;
}

export const SectionTitle = ({
  children,
  component = 'h2',
  showDivider = false,
}: SectionTitleProps) => {
  if (!showDivider) {
    return (
      <Typography variant="h3" component={component} gutterBottom sx={{ color: 'primary.main' }}>
        {children}
      </Typography>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2.5, px: 0.5 }}>
      <Typography variant="h3" component={component} sx={{ color: 'primary.main' }}>
        {children}
      </Typography>
      <Box
        sx={(theme) => ({
          height: '1px',
          flex: 1,
          background: `linear-gradient(to right, ${theme.palette.secondary.light}, transparent)`,
        })}
      />
    </Box>
  );
};
