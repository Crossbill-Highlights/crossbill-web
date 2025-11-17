/**
 * Crossbill Obsidian Plugin
 * Imports highlights from Crossbill into Obsidian notes
 */

import { Editor, Notice, Plugin } from 'obsidian';
import { CrossbillAPI } from './api';
import { formatBook, formatBookHeader, formatChapter, formatHighlight } from './formatters';
import { BookSuggestModal, ChapterSuggestModal, HighlightSuggestModal } from './modals';
import { CrossbillSettingTab } from './settings';
import {
  BookDetails,
  CrossbillSettings,
  DEFAULT_SETTINGS,
  HighlightWithChapterInfo,
} from './types';

export default class CrossbillPlugin extends Plugin {
  settings: CrossbillSettings;
  api: CrossbillAPI;

  async onload() {
    await this.loadSettings();
    this.api = new CrossbillAPI(this.settings.serverHost);

    // Add command to import highlights from a single chapter
    this.addCommand({
      id: 'import-chapter-highlights',
      name: 'Import highlights from a chapter',
      editorCallback: (editor: Editor) => {
        this.importChapterHighlights(editor);
      },
    });

    // Add command to import all highlights from a book
    this.addCommand({
      id: 'import-all-highlights',
      name: 'Import all highlights from a book',
      editorCallback: (editor: Editor) => {
        this.importAllChapters(editor);
      },
    });

    // Add command to import a single highlight from a book
    this.addCommand({
      id: 'import-single-highlight',
      name: 'Import a single highlight from a book',
      editorCallback: (editor: Editor) => {
        this.importSingleHighlight(editor);
      },
    });

    // Add settings tab
    this.addSettingTab(new CrossbillSettingTab(this.app, this));
  }

  /**
   * Select a book from the list and fetch its details
   */
  private async selectBook(onBookSelected: (book: BookDetails) => void) {
    try {
      const booksResponse = await this.api.getBooks();
      if (booksResponse.books.length === 0) {
        new Notice('No books found in Crossbill');
        return;
      }

      new BookSuggestModal(this.app, booksResponse.books, async (selectedBook) => {
        try {
          const bookDetails = await this.api.getBookDetails(selectedBook.id);

          if (bookDetails.chapters.length === 0) {
            new Notice('No chapters found for this book');
            return;
          }

          onBookSelected(bookDetails);
        } catch (error) {
          new Notice(`Error fetching book details: ${error.message}`);
          console.error('Error fetching book details:', error);
        }
      }).open();
    } catch (error) {
      new Notice(`Error fetching books: ${error.message}`);
      console.error('Error fetching books:', error);
    }
  }

  /**
   * Import highlights from a single chapter
   */
  async importChapterHighlights(editor: Editor) {
    await this.selectBook((bookDetails) => {
      // Show chapter selection modal
      new ChapterSuggestModal(this.app, bookDetails.chapters, (selectedChapter) => {
        try {
          const content = formatBookHeader(bookDetails) + formatChapter(selectedChapter, true);

          const cursor = editor.getCursor();
          editor.replaceRange(content, cursor);

          new Notice(
            `Imported ${selectedChapter.highlights.length} highlights from "${selectedChapter.name}"`
          );
        } catch (error) {
          new Notice(`Error inserting highlights: ${error.message}`);
          console.error('Error inserting highlights:', error);
        }
      }).open();
    });
  }

  /**
   * Import all highlights from all chapters of a book
   */
  async importAllChapters(editor: Editor) {
    await this.selectBook((bookDetails) => {
      try {
        const content = formatBook(bookDetails);

        const cursor = editor.getCursor();
        editor.replaceRange(content, cursor);

        // Calculate total highlights across all chapters
        const totalHighlights = bookDetails.chapters.reduce(
          (sum, chapter) => sum + chapter.highlights.length,
          0
        );

        new Notice(
          `Imported ${totalHighlights} highlights from ${bookDetails.chapters.length} chapters of "${bookDetails.title}"`
        );
      } catch (error) {
        new Notice(`Error inserting highlights: ${error.message}`);
        console.error('Error inserting highlights:', error);
      }
    });
  }

  /**
   * Import a single highlight from a book
   */
  async importSingleHighlight(editor: Editor) {
    await this.selectBook((bookDetails) => {
      // Collect all highlights from all chapters with chapter info
      const allHighlights: HighlightWithChapterInfo[] = [];

      bookDetails.chapters.forEach((chapter) => {
        chapter.highlights.forEach((highlight) => {
          allHighlights.push({
            ...highlight,
            chapterName: chapter.name,
          });
        });
      });

      if (allHighlights.length === 0) {
        new Notice('No highlights found in this book');
        return;
      }

      // Show highlight selection modal
      new HighlightSuggestModal(this.app, allHighlights, (selectedHighlight) => {
        try {
          const content = formatHighlight(selectedHighlight, bookDetails.title);

          const cursor = editor.getCursor();
          editor.replaceRange(content, cursor);

          new Notice(`Imported highlight from "${selectedHighlight.chapterName}"`);
        } catch (error) {
          new Notice(`Error inserting highlight: ${error.message}`);
          console.error('Error inserting highlight:', error);
        }
      }).open();
    });
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.api = new CrossbillAPI(this.settings.serverHost);
  }

  async saveSettings() {
    await this.saveData(this.settings);
    this.api = new CrossbillAPI(this.settings.serverHost);
  }
}
