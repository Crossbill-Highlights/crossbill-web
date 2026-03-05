import { FilterListIcon } from '@/theme/Icons';
import Fab from '@mui/material/Fab';

export const FilterFab = ({
  filterEnabled,
  onClick,
}: {
  filterEnabled: boolean;
  onClick: () => void;
}) => {
  return (
    <Fab
      size="small"
      color={filterEnabled ? 'primary' : 'default'}
      aria-label="Open filters"
      onClick={() => onClick()}
      sx={{
        position: 'fixed',
        bottom: 'calc(80px + env(safe-area-inset-bottom))',
        right: 24,
        zIndex: 1000,
      }}
    >
      <FilterListIcon />
    </Fab>
  );
};
