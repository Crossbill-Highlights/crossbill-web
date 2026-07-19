import { Box, useTheme } from '@mui/material';
import { motion } from 'motion/react';

interface ProgressBarProps {
  currentIndex: number;
  totalCount: number;
}

export const ProgressBar = ({ currentIndex, totalCount }: ProgressBarProps) => {
  const theme = useTheme();
  const progressPercentage = ((currentIndex + 1) / totalCount) * 100;

  return (
    <Box
      sx={{
        width: '100%',
        height: '4px',
        backgroundColor: theme.customColors.backgrounds.subtle,
        overflow: 'hidden',
        mt: 0,
      }}
    >
      <motion.div
        style={{
          height: '100%',
          backgroundColor: theme.palette.primary.main,
          transformOrigin: 'left',
        }}
        initial={{ width: `${progressPercentage}%` }}
        animate={{ width: `${progressPercentage}%` }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
      />
    </Box>
  );
};
