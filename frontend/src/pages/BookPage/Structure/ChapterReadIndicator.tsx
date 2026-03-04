import { useTheme } from '@mui/material';

type ReadStatus = 'read' | 'current' | 'unread';

interface ChapterReadIndicatorProps {
  status: ReadStatus;
}

const SIZE = 16;

export const ChapterReadIndicator = ({ status }: ChapterReadIndicatorProps) => {
  const theme = useTheme();
  const brown = theme.palette.secondary.dark;
  const gray = theme.palette.text.disabled;

  return (
    <svg
      width={SIZE}
      height={SIZE}
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      style={{ flexShrink: 0, display: 'block' }}
    >
      {status === 'read' && <circle cx={8} cy={8} r={6} fill={brown} />}
      {status === 'current' && (
        <>
          <circle cx={8} cy={8} r={6} fill="none" stroke={brown} strokeWidth={1.5} />
          <circle cx={8} cy={8} r={3} fill={brown} />
        </>
      )}
      {status === 'unread' && (
        <circle cx={8} cy={8} r={6} fill="none" stroke={gray} strokeWidth={1.5} />
      )}
    </svg>
  );
};
