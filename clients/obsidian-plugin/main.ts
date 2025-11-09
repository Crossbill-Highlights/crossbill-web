import { App, Editor, Notice, Plugin, PluginSettingTab, Setting, SuggestModal } from 'obsidian';

// Types based on Crossbill API
interface Book {
  id: number;
  title: string;
  author: string | null;
  isbn: string | null;
  created_at: string;
  updated_at: string;
}

interface BookWithHighlightCount extends Book {
  highlight_count: number;
}

interface BooksListResponse {
  books: BookWithHighlightCount[];
  total: number;
  offset: number;
  limit: number;
}

interface Highlight {
  id: number;
  book_id: number;
  chapter_id: number | null;
  text: string;
  chapter: string | null;
  page: number | null;
  note: string | null;
  datetime: string;
  created_at: string;
  updated_at: string;
}

interface Chapter {
  id: number;
  book_id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

interface ChapterWithHighlights extends Chapter {
  highlights: Highlight[];
}

interface BookDetails extends Book {
  chapters: ChapterWithHighlights[];
}

// Plugin Settings
interface CrossbillSettings {
  serverHost: string;
}

const DEFAULT_SETTINGS: CrossbillSettings = {
  serverHost: 'http://localhost:8000',
};

// API Client
class CrossbillAPI {
  constructor(private serverHost: string) {}

  async getBooks(): Promise<BooksListResponse> {
    const response = await fetch(`${this.serverHost}/api/v1/highlights/books?limit=1000`);
    if (!response.ok) {
      throw new Error(`Failed to fetch books: ${response.statusText}`);
    }
    return await response.json();
  }

  async getBookDetails(bookId: number): Promise<BookDetails> {
    const response = await fetch(`${this.serverHost}/api/v1/book/${bookId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch book details: ${response.statusText}`);
    }
    return await response.json();
  }
}

// Book Selection Modal
class BookSuggestModal extends SuggestModal<BookWithHighlightCount> {
  private books: BookWithHighlightCount[];
  private onSelect: (book: BookWithHighlightCount) => void;

  constructor(
    app: App,
    books: BookWithHighlightCount[],
    onSelect: (book: BookWithHighlightCount) => void
  ) {
    super(app);
    this.books = books;
    this.onSelect = onSelect;
    this.setPlaceholder('Select a book...');
  }

  getSuggestions(query: string): BookWithHighlightCount[] {
    const lowerQuery = query.toLowerCase();
    return this.books.filter((book) => {
      const title = book.title.toLowerCase();
      const author = book.author?.toLowerCase() || '';
      return title.includes(lowerQuery) || author.includes(lowerQuery);
    });
  }

  renderSuggestion(book: BookWithHighlightCount, el: HTMLElement) {
    el.createEl('div', { text: book.title, cls: 'crossbill-book-title' });
    if (book.author) {
      el.createEl('small', { text: book.author, cls: 'crossbill-book-author' });
    }
    el.createEl('small', {
      text: ` (${book.highlight_count} highlights)`,
      cls: 'crossbill-highlight-count',
    });
  }

  onChooseSuggestion(book: BookWithHighlightCount) {
    this.onSelect(book);
  }
}

// Chapter Selection Modal
class ChapterSuggestModal extends SuggestModal<ChapterWithHighlights> {
  private chapters: ChapterWithHighlights[];
  private onSelect: (chapter: ChapterWithHighlights) => void;

  constructor(
    app: App,
    chapters: ChapterWithHighlights[],
    onSelect: (chapter: ChapterWithHighlights) => void
  ) {
    super(app);
    this.chapters = chapters;
    this.onSelect = onSelect;
    this.setPlaceholder('Select a chapter...');
  }

  getSuggestions(query: string): ChapterWithHighlights[] {
    const lowerQuery = query.toLowerCase();
    return this.chapters.filter((chapter) => chapter.name.toLowerCase().includes(lowerQuery));
  }

  renderSuggestion(chapter: ChapterWithHighlights, el: HTMLElement) {
    el.createEl('div', { text: chapter.name, cls: 'crossbill-chapter-name' });
    el.createEl('small', {
      text: ` (${chapter.highlights.length} highlights)`,
      cls: 'crossbill-highlight-count',
    });
  }

  onChooseSuggestion(chapter: ChapterWithHighlights) {
    this.onSelect(chapter);
  }
}

// Settings Tab
class CrossbillSettingTab extends PluginSettingTab {
  plugin: CrossbillPlugin;

  constructor(app: App, plugin: CrossbillPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'Crossbill Settings' });

    new Setting(containerEl)
      .setName('Server Host')
      .setDesc('The URL of your Crossbill server (e.g., http://localhost:8000)')
      .addText((text) =>
        text
          .setPlaceholder('http://localhost:8000')
          .setValue(this.plugin.settings.serverHost)
          .onChange(async (value) => {
            this.plugin.settings.serverHost = value;
            await this.plugin.saveSettings();
          })
      );
  }
}

// Main Plugin
export default class CrossbillPlugin extends Plugin {
  settings: CrossbillSettings;
  api: CrossbillAPI;

  async onload() {
    await this.loadSettings();
    this.api = new CrossbillAPI(this.settings.serverHost);

    // Add command to import highlights from a single chapter
    this.addCommand({
      id: 'import-highlights',
      name: 'Import highlights from a chapter',
      editorCallback: (editor: Editor) => {
        this.importChapterHighlights(editor);
      },
    });

    // Add settings tab
    this.addSettingTab(new CrossbillSettingTab(this.app, this));
  }

  /**
   * Format a single highlight with its note and page number
   */
  private formatHighlight(highlight: Highlight): string {
    let content = '';

    content += `> ${highlight.text}\n\n`;

    if (highlight.note) {
      content += `**Note:** ${highlight.note}\n\n`;
    }

    if (highlight.page !== null) {
      content += `*Page ${highlight.page}*\n\n`;
    }

    content += '---\n\n';

    return content;
  }

  /**
   * Format book header with title and author
   */
  private formatBookHeader(book: Book): string {
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
  private formatChapter(chapter: ChapterWithHighlights, includeChapterHeader = true): string {
    let content = '';

    if (includeChapterHeader) {
      content += `### ${chapter.name}\n\n`;
    }

    chapter.highlights.forEach((highlight) => {
      content += this.formatHighlight(highlight);
    });

    return content;
  }

  /**
   * Format entire book with all chapters and highlights
   */
  private formatBook(book: BookDetails): string {
    let content = this.formatBookHeader(book);

    book.chapters.forEach((chapter) => {
      content += this.formatChapter(chapter, true);
    });

    return content;
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
          const content =
            this.formatBookHeader(bookDetails) + this.formatChapter(selectedChapter, true);

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

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.api = new CrossbillAPI(this.settings.serverHost);
  }

  async saveSettings() {
    await this.saveData(this.settings);
    this.api = new CrossbillAPI(this.settings.serverHost);
  }
}
