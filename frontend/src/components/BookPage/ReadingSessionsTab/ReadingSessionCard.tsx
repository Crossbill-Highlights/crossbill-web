import type { ReadingSession } from '@/api/generated/model';
import { DateIcon, DurationIcon, TimeIcon } from '@/components/common/Icons.tsx';
import { formatDate, formatDuration, formatTime } from '@/utils/date';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import { Box, Typography } from '@mui/material';

interface SessionDateProps {
  startTime: string;
}

const SessionDate = ({ startTime }: SessionDateProps) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <DateIcon
      sx={{
        fontSize: 18,
        color: 'primary.main',
        opacity: 0.7,
      }}
    />
    <Typography variant="body1">{formatDate(startTime)}</Typography>
  </Box>
);

interface SessionStartTimeProps {
  startTime: string;
}

const SessionStartTime = ({ startTime }: SessionStartTimeProps) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <TimeIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
    <Typography variant="body2" color="text.secondary">
      {formatTime(startTime)}
    </Typography>
  </Box>
);

interface SessionDurationProps {
  startTime: string;
  endTime: string;
}

const SessionDuration = ({ startTime, endTime }: SessionDurationProps) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <DurationIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
    <Typography variant="body2" color="text.secondary">
      {formatDuration(startTime, endTime)}
    </Typography>
  </Box>
);

interface SessionPageRangeProps {
  startPage: number;
  endPage: number;
}

const SessionPageRange = ({ startPage, endPage }: SessionPageRangeProps) => {
  const pagesRead = endPage - startPage;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        mt: 1.5,
        pl: 0.5,
      }}
    >
      <MenuBookIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
      <Typography variant="caption" color="text.secondary">
        Pages {startPage} - {endPage}
        {pagesRead > 0 && ` (${pagesRead} pages)`}
      </Typography>
    </Box>
  );
};

interface ReadingSessionCardProps {
  session: ReadingSession;
}

export const ReadingSessionCard = ({ session }: ReadingSessionCardProps) => {
  const hasPageInfo = session.start_page != null && session.end_page != null;

  return (
    <Box
      sx={{
        py: 2.5,
        px: 2.5,
        borderBottom: 1,
        borderColor: 'divider',
        '&:last-child': {
          borderBottom: 0,
        },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 3,
          flexWrap: 'wrap',
        }}
      >
        <SessionDate startTime={session.start_time} />
        <SessionStartTime startTime={session.start_time} />
        <SessionDuration startTime={session.start_time} endTime={session.end_time} />
      </Box>

      {hasPageInfo && (
        <SessionPageRange startPage={session.start_page!} endPage={session.end_page!} />
      )}
    </Box>
  );
};
