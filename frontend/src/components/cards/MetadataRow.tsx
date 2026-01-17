import type { SxProps, Theme, TypographyProps } from '@mui/material';
import { Typography } from '@mui/material';
import { Fragment, type ReactNode } from 'react';

interface MetadataRowProps {
  items: ReactNode[];
  variant?: TypographyProps['variant'];
  sx?: SxProps<Theme>;
}

export const MetadataRow = ({ items, variant = 'body2', sx }: MetadataRowProps) => {
  const validItems = items.filter(
    (item) => item !== null && item !== undefined && item !== false && item !== ''
  );

  if (validItems.length === 0) {
    return null;
  }

  const defaultSx: SxProps<Theme> = {
    color: 'text.secondary',
  };

  return (
    <Typography variant={variant} sx={sx || defaultSx}>
      {validItems.map((item, index) => (
        <Fragment key={index}>
          <span>{item}</span>
          {index < validItems.length - 1 && <span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>}
        </Fragment>
      ))}
    </Typography>
  );
};
