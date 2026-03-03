import { ExpandMoreIcon } from '@/theme/Icons.tsx';
import { Accordion, AccordionDetails, AccordionSummary, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface CollapsibleSectionProps {
  title: string;
  count?: number;
  defaultExpanded?: boolean;
  children: ReactNode;
}

export const CollapsibleSection = ({
  title,
  count,
  defaultExpanded = false,
  children,
}: CollapsibleSectionProps) => {
  const headerText = count !== undefined ? `${title} (${count})` : title;

  return (
    <Accordion
      defaultExpanded={defaultExpanded}
      sx={{
        boxShadow: 'none',
        '&:before': { display: 'none' },
        '&.Mui-expanded': { m: 0 },
        bgcolor: 'transparent',
        borderBottom: '1px solid',
        borderColor: 'divider',
        '&:last-of-type': { borderBottom: 'none', borderRadius: 0 },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          '&.Mui-expanded': { minHeight: 48 },
          '& .MuiAccordionSummary-content.Mui-expanded': { my: '12px' },
        }}
      >
        <Typography variant="body1" sx={{ fontWeight: 600, color: 'primary.main' }}>
          {headerText}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 0 }}>{children}</AccordionDetails>
    </Accordion>
  );
};
