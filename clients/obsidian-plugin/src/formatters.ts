/**
 * Formatting utilities for converting highlights to Markdown
 */

import { Book, Highlight, ChapterWithHighlights, BookDetails } from './types';

/**
 * Format a single highlight with its note, page number, and tags
 * @param highlight - The highlight to format
 * @param bookTitle - Optional book title to display (for single highlight imports)
 */
export function formatHighlight(highlight: Highlight, bookTitle?: string): string {
  let content = '';

  content += `> ${highlight.text}\n\n`;

  if (highlight.note) {
    content += `**Note:** ${highlight.note}\n\n`;
  }

  if (highlight.page !== null) {
    content += `*Page ${highlight.page}*\n\n`;
  }

  if (bookTitle) {
    content += `*${bookTitle}*\n\n`;
  }

  // Add tags in Obsidian format (#tagname)
  if (highlight.highlight_tags && highlight.highlight_tags.length > 0) {
    const tags = highlight.highlight_tags.map((tag) => `#${tag.name}`).join(' ');
    content += `${tags}\n\n`;
  }

  content += '---\n\n';

  return content;
}

/**
 * Format book header with title and author
 */
export function formatBookHeader(book: Book): string {
  let content = `## ${book.title}\n`;
  if (book.author) {
    content += `**Author:** ${book.author}\n\n`;
  } else {
    content += '\n';
  }
  return content;
}

/**
 * Format a chapter with all its highlights
 */
export function formatChapter(chapter: ChapterWithHighlights, includeChapterHeader = true): string {
  let content = '';

  if (includeChapterHeader) {
    content += `### ${chapter.name}\n\n`;
  }

  chapter.highlights.forEach((highlight) => {
    content += formatHighlight(highlight);
  });

  return content;
}

/**
 * Format entire book with all chapters and highlights
 */
export function formatBook(book: BookDetails): string {
  let content = formatBookHeader(book);

  book.chapters.forEach((chapter) => {
    content += formatChapter(chapter, true);
  });

  return content;
}
