import { Box } from '@mui/material';
import { motion } from 'motion/react';

interface ProgressBarProps {
  currentIndex: number;
  totalCount: number;
}

export const ProgressBar = ({ currentIndex, totalCount }: ProgressBarProps) => {
  const progressPercentage = ((currentIndex + 1) / totalCount) * 100;

  return (
    <Box
      sx={{
        width: '100%',
        height: '4px',
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        overflow: 'hidden',
        mt: 0,
      }}
    >
      <motion.div
        style={{
          height: '100%',
          backgroundColor: '#43311E', // primary.main (amber.700)
          transformOrigin: 'left',
        }}
        initial={{ width: `${progressPercentage}%` }}
        animate={{ width: `${progressPercentage}%` }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
      />
    </Box>
  );
};
