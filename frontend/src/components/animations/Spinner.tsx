import { Box, CircularProgress } from '@mui/material';

export interface SpinnerProps {
  size?: number;
}

export const Spinner = ({ size = 40 }: SpinnerProps) => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 200,
      }}
    >
      <CircularProgress size={size} />
    </Box>
  );
};
