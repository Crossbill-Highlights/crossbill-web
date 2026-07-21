import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import { CollapsibleSection } from '@/pages/BookPage/Structure/ChapterDetailDialog/CollapsibleSection';
import { Box, Stack, Typography } from '@mui/material';

interface ChapterGistsContextProps {
  bookId: number;
}

/**
 * Read-only recap of the reader's chapter gists, collapsed by default, offered
 * as context while answering the reflection questions. Never copied into a field.
 */
export const ChapterGistsContext = ({ bookId }: ChapterGistsContextProps) => {
  const { data } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, { kind: 'gist' });
  const gists = data?.items ?? [];

  if (gists.length === 0) return null;

  return (
    <CollapsibleSection title="Your chapter gists" count={gists.length}>
      <Stack gap={1.5}>
        {gists.map((gist) => {
          const chapterName = gist.chapters?.[0]?.name;
          return (
            <Box key={gist.id}>
              {chapterName && (
                <Typography variant="subtitle2" color="text.secondary">
                  {chapterName}
                </Typography>
              )}
              <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                {gist.body}
              </Typography>
            </Box>
          );
        })}
      </Stack>
    </CollapsibleSection>
  );
};
