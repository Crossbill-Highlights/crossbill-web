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

    // Add command to import highlights
    this.addCommand({
      id: 'import-highlights',
      name: 'Import highlights from Crossbill',
      editorCallback: (editor: Editor) => {
        this.importHighlights(editor);
      },
    });

    // Add settings tab
    this.addSettingTab(new CrossbillSettingTab(this.app, this));
  }

  async importHighlights(editor: Editor) {
    try {
      // Step 1: Fetch and select book
      const booksResponse = await this.api.getBooks();
      if (booksResponse.books.length === 0) {
        new Notice('No books found in Crossbill');
        return;
      }

      new BookSuggestModal(this.app, booksResponse.books, async (selectedBook) => {
        try {
          // Step 2: Fetch book details with chapters
          const bookDetails = await this.api.getBookDetails(selectedBook.id);

          if (bookDetails.chapters.length === 0) {
            new Notice('No chapters found for this book');
            return;
          }

          // Step 3: Select chapter
          new ChapterSuggestModal(this.app, bookDetails.chapters, async (selectedChapter) => {
            try {
              // Step 4: Format and insert highlights
              this.insertHighlights(editor, selectedBook, selectedChapter);
            } catch (error) {
              new Notice(`Error inserting highlights: ${error.message}`);
              console.error('Error inserting highlights:', error);
            }
          }).open();
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

  insertHighlights(editor: Editor, book: BookWithHighlightCount, chapter: ChapterWithHighlights) {
    const cursor = editor.getCursor();
    let content = '';

    // Add header
    content += `## ${book.title}\n`;
    if (book.author) {
      content += `**Author:** ${book.author}\n`;
    }
    content += `**Chapter:** ${chapter.name}\n\n`;

    // Add highlights
    chapter.highlights.forEach((highlight, index) => {
      content += `### Highlight ${index + 1}\n`;
      content += `> ${highlight.text}\n\n`;

      if (highlight.note) {
        content += `**Note:** ${highlight.note}\n\n`;
      }

      if (highlight.page !== null) {
        content += `*Page ${highlight.page}*\n\n`;
      }

      content += '---\n\n';
    });

    editor.replaceRange(content, cursor);
    new Notice(`Imported ${chapter.highlights.length} highlights from "${chapter.name}"`);
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
