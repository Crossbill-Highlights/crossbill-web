import type { BookDetails, ChapterWithHighlights } from '@/api/generated/model';
import { ThreeColumnLayout } from '@/components/layout/Layouts';
import { Box, Typography } from '@mui/material';
import { ChapterAccordion } from './ChapterAccordion';

interface StructureTabProps {
  book: BookDetails;
  isDesktop: boolean;
}

export const StructureTab = ({ book, isDesktop }: StructureTabProps) => {
  if (book.chapters.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No chapter structure available for this book.
        </Typography>
      </Box>
    );
  }

  const topLevelChapters = book.chapters.filter((ch: ChapterWithHighlights) => !ch.parent_id);

  const content = (
    <Box>
      {topLevelChapters.map((chapter) => (
        <ChapterAccordion key={chapter.id} chapter={chapter} allChapters={book.chapters} />
      ))}
    </Box>
  );

  if (!isDesktop) {
    return <Box sx={{ maxWidth: '800px', mx: 'auto' }}>{content}</Box>;
  }

  return (
    <ThreeColumnLayout>
      <div></div>
      {content}
      <div></div>
    </ThreeColumnLayout>
  );
};
