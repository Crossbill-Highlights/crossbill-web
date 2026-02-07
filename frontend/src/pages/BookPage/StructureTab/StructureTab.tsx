import type { BookDetails } from '@/api/generated/model';
import { Box, Typography } from '@mui/material';
import { ChapterAccordion } from './ChapterAccordion';

interface StructureTabProps {
  book: BookDetails;
}

export const StructureTab = ({ book }: StructureTabProps) => {
  if (book.chapters.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No chapter structure available for this book.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', maxWidth: '800px', mx: 'auto' }}>
      {book.chapters.map((chapter) => (
        <ChapterAccordion key={chapter.id} chapter={chapter} />
      ))}
    </Box>
  );
};
