import { useTheme } from '@mui/material';

type ReadStatus = 'read' | 'current' | 'unread';

interface ChapterReadIndicatorProps {
  status: ReadStatus;
}

const SIZE = 20;

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
      {status === 'read' && (
        <>
          <circle cx={10} cy={10} r={8} fill={brown} />
          <path
            d="M6 10.5 L9 13.5 L14.5 7"
            fill="none"
            stroke="white"
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </>
      )}
      {status === 'current' && (
        <>
          <circle cx={10} cy={10} r={7.5} fill="none" stroke={brown} strokeWidth={1.5} />
          <circle cx={10} cy={10} r={3.5} fill={brown} />
        </>
      )}
      {status === 'unread' && (
        <circle cx={10} cy={10} r={7.5} fill="none" stroke={gray} strokeWidth={1.5} />
      )}
    </svg>
  );
};
