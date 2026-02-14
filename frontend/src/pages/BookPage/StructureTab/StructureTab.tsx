import type {
  BookDetails,
  ChapterPrereadingResponse,
  ChapterWithHighlights,
} from '@/api/generated/model';
import { useGetBookPrereadingApiV1BooksBookIdPrereadingGet } from '@/api/generated/prereading/prereading';
import { ThreeColumnLayout } from '@/components/layout/Layouts';
import { Box, Typography } from '@mui/material';
import { useMemo } from 'react';
import { ChapterAccordion } from './ChapterAccordion';
import { ReadingProgressLine } from './ReadingProgressLine';

interface StructureTabProps {
  book: BookDetails;
  isDesktop: boolean;
}

export const StructureTab = ({ book, isDesktop }: StructureTabProps) => {
  const { data: bookPrereading } = useGetBookPrereadingApiV1BooksBookIdPrereadingGet(book.id);

  const prereadingByChapterId = useMemo(() => {
    const map: Record<number, ChapterPrereadingResponse> = {};
    if (bookPrereading?.items) {
      for (const item of bookPrereading.items) {
        map[item.chapter_id] = item;
      }
    }
    return map;
  }, [bookPrereading]);

  const childrenByParentId = useMemo(() => {
    const map = new Map<number | null, ChapterWithHighlights[]>();
    for (const ch of book.chapters) {
      const key = ch.parent_id ?? null;
      const list = map.get(key) ?? [];
      list.push(ch);
      map.set(key, list);
    }
    return map;
  }, [book.chapters]);

  if (book.chapters.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No chapter structure available for this book.
        </Typography>
      </Box>
    );
  }

  const topLevelChapters = childrenByParentId.get(null) ?? [];

  const readingPosition = book.reading_position;

  const isChapterRead = (startPosition: { index: number } | null | undefined): boolean => {
    if (!readingPosition || !startPosition) return false;
    return readingPosition.index >= startPosition.index;
  };

  const content = (
    <ReadingProgressLine readingPosition={readingPosition}>
      {topLevelChapters.map((chapter) => (
        <ChapterAccordion
          key={chapter.id}
          chapter={chapter}
          childrenByParentId={childrenByParentId}
          bookId={book.id}
          prereadingByChapterId={prereadingByChapterId}
          isRead={isChapterRead(chapter.start_position)}
          readingPosition={readingPosition}
          preExpanded={true}
        />
      ))}
    </ReadingProgressLine>
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
