import type { SvgIconComponent } from '@mui/icons-material';
import { Box, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface SidebarSectionHeaderProps {
  icon: SvgIconComponent;
  title: string;
  action?: ReactNode;
}

export const SidebarSectionHeader = ({ icon: Icon, title, action }: SidebarSectionHeaderProps) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      mb: 2,
    }}
  >
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Icon sx={{ fontSize: 18, color: 'primary.main' }} />
      <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
        {title}
      </Typography>
    </Box>
    {action}
  </Box>
);
