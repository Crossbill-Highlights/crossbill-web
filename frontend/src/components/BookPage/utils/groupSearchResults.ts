import type { Highlight, HighlightSearchResult } from '@/api/generated/model';
import { chain, sortBy } from 'lodash';

/**
 * Groups search results by chapter and sorts them appropriately.
 * Converts HighlightSearchResult[] to ChapterData[] format.
 * TODO: maybe this can be removed if we just returned highlights grouped by chapter from the backend?
 */
export function groupSearchResultsIntoChapters(highlights: HighlightSearchResult[] | undefined): {
  id: string | number;
  name: string;
  chapterNumber: number | undefined;
  highlights: Highlight[];
}[] {
  if (!highlights || highlights.length === 0) {
    return [];
  }

  return chain(highlights)
    .groupBy((highlight) => highlight.chapter_id ?? 'null')
    .map((chapterHighlights, chapterIdStr) => ({
      id: chapterIdStr === 'null' ? 'unknown' : Number(chapterIdStr),
      name: chapterHighlights[0]?.chapter_name ?? 'Unknown Chapter',
      chapterNumber: chapterHighlights[0]?.chapter_number ?? undefined,
      highlights: sortBy(
        chapterHighlights,
        (highlight) => highlight.page ?? Infinity
      ) as unknown as Highlight[],
    }))
    .sortBy((chapter) => {
      // Sort by chapter_number if available, otherwise by chapter_id
      // Chapters without number go to the end
      if (chapter.chapterNumber !== null && chapter.chapterNumber !== undefined) {
        return chapter.chapterNumber;
      }
      const numericId = typeof chapter.id === 'number' ? chapter.id : 0;
      return numericId + 1000000; // Large offset to put them at the end
    })
    .value();
}
