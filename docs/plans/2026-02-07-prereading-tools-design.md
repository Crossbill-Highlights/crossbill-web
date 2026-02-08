# Pre-reading Tools Design

**Date:** 2026-02-07
**Status:** Design Approved
**Feature:** Pre-reading tools with book structure view and AI-generated keypoints

## Overview

Add a pre-reading feature that helps users skim a book's structure and understand what they're about to read before diving in. Users can view the hierarchical table of contents and generate AI-powered summaries and keypoints for each chapter to set their reading expectations.

## Goals

- Help users set expectations before reading
- Inspire readers to think about what they're going to read
- Provide quick overview of chapter content without reading highlights
- Leverage existing EPUB content and AI capabilities
- Mobile-friendly interface for on-the-go pre-reading

## User Experience

### Workflow

1. User navigates to a book page
2. Clicks on new "Structure" (or "Overview") tab
3. Sees hierarchical chapter structure displayed as accordions
4. Expands a chapter of interest
5. Sees a "Generate Pre-reading Overview" button
6. Clicks button → system generates summary and keypoints (5-30 seconds)
7. Views the generated content:
   - Brief paragraph summary (2-3 sentences)
   - 3-5 bullet-point keypoints
   - Metadata (AI model used, generation timestamp)
8. Next visit → content is already there (cached in database)

### UI Location

New tab on the book page (alongside Highlights, Flashcards, Reading Sessions).

### Display Pattern

**Accordion sections** - Top-level chapters as accordion headers, sub-chapters nested inside. Mobile-friendly, clean, handles complex book structures well.

### Generation Scope

All chapters can generate keypoints (user decides). If a chapter has minimal/no text, AI will indicate this or work with whatever exists.

## Architecture

Following Crossbill's DDD (Domain-Driven Design) with hexagonal architecture.

### Domain Layer

**New Entity: ChapterPrereadingContent**

Location: `backend/src/domain/reading/entities/chapter_prereading_content.py`

```python
@dataclass
class ChapterPrereadingContent(Entity[PrereadingContentId]):
    id: PrereadingContentId
    chapter_id: ChapterId
    summary: str  # Brief paragraph summary
    keypoints: list[str]  # 3-5 bullet points
    generated_at: datetime
    ai_model: str  # Track which AI model generated it
```

**Why reading domain?** Pre-reading is part of the reading experience (like highlights, bookmarks, sessions), not library management.

**Why separate entity?**
- Not all chapters will have pre-reading content (on-demand generation)
- Keeps Chapter entity focused on structural metadata
- Allows tracking generation metadata
- Easy to delete/regenerate

**Relationship:** One-to-one (Chapter → ChapterPrereadingContent, optional)

### Application Layer

**New Use Case: ChapterPrereadingUseCase**

Location: `backend/src/application/reading/use_cases/chapter_prereading_use_case.py`

```python
class ChapterPrereadingUseCase:
    def __init__(
        self,
        prereading_repo: ChapterPrereadingRepository,
        chapter_repo: ChapterRepository,
        text_extraction_service: EbookTextExtractionService,
        ai_service: AIService,
    ):
        ...

    def get_prereading_content(
        self, chapter_id: ChapterId, user_id: UserId
    ) -> ChapterPrereadingContent | None:
        """Get existing pre-reading content if available."""

    def generate_prereading_content(
        self, chapter_id: ChapterId, user_id: UserId
    ) -> ChapterPrereadingContent:
        """Generate new pre-reading content for a chapter.

        Steps:
        1. Verify chapter ownership via chapter_repo
        2. Get chapter with XPoint data
        3. Extract chapter text using EbookTextExtractionService
        4. Call AI service to generate summary + keypoints
        5. Create ChapterPrereadingContent entity (includes ai_model from AI response)
        6. Save via prereading_repo
        7. Return the entity
        """
```

**Prerequisite:** Chapters must have `start_xpoint` and `end_xpoint` stored in database (see Enhancement section below).

### Infrastructure Layer

**Repository Implementation**

Location: `backend/src/infrastructure/reading/repositories/chapter_prereading_repository.py`

```python
class ChapterPrereadingRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_chapter_id(
        self, chapter_id: ChapterId
    ) -> ChapterPrereadingContent | None:
        """Find existing pre-reading content for a chapter."""

    def save(self, content: ChapterPrereadingContent) -> None:
        """Save or update pre-reading content."""
```

**Database Schema**

New table: `chapter_prereading_contents`

```sql
CREATE TABLE chapter_prereading_contents (
    id UUID PRIMARY KEY,
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    keypoints JSONB NOT NULL,  -- Array of strings
    generated_at TIMESTAMP NOT NULL,
    ai_model VARCHAR(100) NOT NULL,
    UNIQUE(chapter_id)  -- One content per chapter
);
```

Enhancement to existing table: `chapters`

```sql
ALTER TABLE chapters
ADD COLUMN start_xpoint TEXT,  -- XPoint string for chapter start
ADD COLUMN end_xpoint TEXT;    -- XPoint string for chapter end (optional)
```

**Router Endpoints**

Location: `backend/src/infrastructure/reading/routers/chapter_prereading.py`

```python
@router.get("/chapters/{chapter_id}/prereading")
async def get_chapter_prereading(
    chapter_id: int,
    use_case: ChapterPrereadingUseCase = Depends(),
    current_user: User = Depends(get_current_user),
) -> ChapterPrereadingResponse | None:
    """Get existing pre-reading content for a chapter."""

@router.post("/chapters/{chapter_id}/prereading/generate")
async def generate_chapter_prereading(
    chapter_id: int,
    use_case: ChapterPrereadingUseCase = Depends(),
    current_user: User = Depends(get_current_user),
) -> ChapterPrereadingResponse:
    """Generate pre-reading content for a chapter (synchronous)."""
```

**Pydantic Schemas**

Location: `backend/src/infrastructure/reading/schemas/chapter_prereading_schemas.py`

```python
class ChapterPrereadingResponse(BaseModel):
    id: str
    chapter_id: str
    summary: str
    keypoints: list[str]
    generated_at: datetime
    ai_model: str
```

### AI Service Integration

**New Pydantic AI Agent**

Add to: `backend/src/infrastructure/ai/ai_agents.py`

```python
class PrereadingContent(BaseModel):
    summary: str
    keypoints: list[str]

def get_prereading_agent() -> Agent[None, PrereadingContent]:
    return Agent(
        get_ai_model(),
        output_type=PrereadingContent,
        instructions="""
        You are helping a reader prepare to read a book chapter.
        Generate pre-reading content to help the reader set expectations and think about
        what they are going to read before they start.

        Generate:
        1. A brief summary (2-3 sentences) of what this chapter covers
        2. 3-5 key points or concepts the reader should watch for

        Focus on helping the reader understand what to expect from the chapter.
        Be concise and specific.
        """,
    )
```

**AI Service Function**

Add to: `backend/src/infrastructure/ai/ai_service.py`

```python
async def get_ai_prereading_from_text(content: str) -> PrereadingContent:
    agent = get_prereading_agent()

    result = await agent.run(content[:10000])  # Limit for token efficiency
    return result.output
```

**Integration notes:**
- Reuses existing AI configuration (Ollama/OpenAI/Anthropic/Gemini)
- No model selection by caller - system decides based on configuration
- AI service returns which model was used (stored in database)
- Synchronous generation (user waits 5-30 seconds)

## Frontend Components

### Structure Tab Component

Location: `frontend/src/pages/BookPage/StructureTab/StructureTab.tsx`

```typescript
export const StructureTab = ({ bookId }: { bookId: number }) => {
  const { data: chapters } = useGetChapters(bookId);

  // Group chapters by top-level (parent_id = null)
  const topLevelChapters = chapters?.filter(ch => !ch.parent_id);

  return (
    <Box>
      {topLevelChapters?.map(chapter => (
        <ChapterAccordion
          key={chapter.id}
          chapter={chapter}
          allChapters={chapters}
        />
      ))}
    </Box>
  );
};
```

### Chapter Accordion Component

Location: `frontend/src/pages/BookPage/StructureTab/ChapterAccordion.tsx`

```typescript
const ChapterAccordion = ({ chapter, allChapters }) => {
  const [expanded, setExpanded] = useState(false);
  const { data: prereading } = useGetChapterPrereading(chapter.id);
  const { mutate: generate, isPending } = useGenerateChapterPrereading();

  const subChapters = allChapters.filter(ch => ch.parent_id === chapter.id);

  return (
    <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
      <AccordionSummary>
        <Typography>{chapter.name}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        {/* Pre-reading content section */}
        <PrereadingContent
          content={prereading}
          onGenerate={() => generate(chapter.id)}
          isGenerating={isPending}
        />

        {/* Nested sub-chapters (recursive) */}
        {subChapters.map(sub => (
          <ChapterAccordion key={sub.id} chapter={sub} allChapters={allChapters} />
        ))}
      </AccordionDetails>
    </Accordion>
  );
};
```

### Pre-reading Content Display

Location: `frontend/src/pages/BookPage/StructureTab/PrereadingContent.tsx`

```typescript
const PrereadingContent = ({
  content,
  onGenerate,
  isGenerating
}: {
  content?: ChapterPrereadingResponse;
  onGenerate: () => void;
  isGenerating: boolean;
}) => {
  if (isGenerating) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Spinner />
        <Typography variant="body2" color="text.secondary">
          Generating pre-reading overview...
        </Typography>
      </Box>
    );
  }

  if (!content) {
    return (
      <Box sx={{ p: 2 }}>
        <Button
          variant="outlined"
          onClick={onGenerate}
          startIcon={<AIIcon />}
        >
          Generate Pre-reading Overview
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
      {/* Summary section */}
      <Typography variant="body1" sx={{ mb: 2 }}>
        {content.summary}
      </Typography>

      {/* Keypoints section */}
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Key Points:
      </Typography>
      <ul>
        {content.keypoints.map((point, idx) => (
          <li key={idx}>
            <Typography variant="body2">{point}</Typography>
          </li>
        ))}
      </ul>

      {/* Metadata */}
      <Typography variant="caption" color="text.secondary">
        Generated by {content.ai_model} on {formatDate(content.generated_at)}
      </Typography>
    </Box>
  );
};
```

### Icon Update

Add to: `frontend/src/theme/Icons.tsx`

```typescript
// Rename AISummaryIcon to AIIcon (more general purpose)
export { AutoAwesome as AIIcon } from '@mui/icons-material';
```

## Error Handling

### Backend Errors

| Error | HTTP Status | User Message | Handling |
|-------|------------|--------------|----------|
| Chapter has no XPoint data | 400 Bad Request | "Chapter position data not available" | Log warning for investigation |
| EPUB file not found | 404 Not Found | "Book file not found" | Already handled by EbookTextExtractionService |
| Text extraction fails | 500 Internal Server Error | "Failed to extract chapter content" | Log error with chapter_id and exception |
| AI service fails | 503 Service Unavailable | "AI service temporarily unavailable" | Log error, consider retry logic |
| AI invalid response | 500 Internal Server Error | "Failed to generate pre-reading content" | Log raw AI response for debugging |
| Unauthorized access | 403 Forbidden | "Access denied" | Already handled by repository patterns |

### Frontend Error Handling

- Show error toast/snackbar with user-friendly message
- Allow retry button for transient failures (AI timeout, network errors)
- Gracefully disable generate button if chapter has no XPoint data

## Testing Strategy

### Backend Tests

**Unit tests:** `backend/tests/unit/application/reading/test_chapter_prereading_use_case.py`
- `test_get_existing_prereading_content()`
- `test_generate_prereading_content_success()`
- `test_generate_prereading_content_chapter_not_found()`
- `test_generate_prereading_content_no_xpoint_data()`
- `test_generate_prereading_content_text_extraction_fails()`
- `test_generate_prereading_content_ai_service_fails()`

**Integration tests:** `backend/tests/integration/reading/test_chapter_prereading_endpoints.py`
- `test_get_prereading_returns_existing_content()`
- `test_get_prereading_returns_null_when_not_generated()`
- `test_generate_prereading_creates_new_content()`
- `test_generate_prereading_returns_403_for_unauthorized_user()`
- `test_generate_prereading_end_to_end_with_real_epub()`

### Frontend Tests

**Component tests:** `frontend/src/pages/BookPage/StructureTab/StructureTab.test.tsx`
- Renders chapter accordion structure
- Displays existing prereading content
- Shows generate button when no content exists
- Handles loading state during generation
- Handles error state on generation failure

### Manual Testing Checklist

- [ ] Upload EPUB with hierarchical TOC (verify XPoint extraction)
- [ ] Generate prereading for top-level chapter
- [ ] Generate prereading for nested sub-chapter
- [ ] Verify content displays correctly
- [ ] Test on mobile (accordion UX)
- [ ] Test with different AI models configured
- [ ] Test error scenarios (missing EPUB, corrupt file)

## Implementation Order

### 1. Database Migrations (Foundation)
- Add `chapter_prereading_contents` table
- Add `start_xpoint`, `end_xpoint` columns to `chapters` table

### 2. Enhance EPUB Chapter Extraction (Critical Prerequisite)
**This must be done first before pre-reading generation will work.**

Update chapter parsing during EPUB upload to:
- Extract XPoint data from TOC entries
- Store `start_xpoint` and `end_xpoint` for each chapter
- Test with various EPUB structures (flat, nested, complex hierarchies)

**Implementation location:** Wherever EPUB TOC parsing currently happens (likely in library services).

**Technical approach:**
- EPUB TOC entries typically contain `content_src` (href to HTML file + optional anchor)
- Convert these to XPoint format that `EbookTextExtractionService` can use
- For end position: use start of next sibling chapter, or end of parent, or end of book

### 3. Backend - Domain & Application Layers
- Create `ChapterPrereadingContent` entity
- Create `PrereadingContentId` value object
- Create `ChapterPrereadingUseCase`
- Add `get_prereading_agent()` to AI agents
- Add `get_ai_prereading_from_text()` to AI service

### 4. Backend - Infrastructure Layer
- Create `ChapterPrereadingRepository`
- Create router endpoints (`chapter_prereading.py`)
- Add Pydantic schemas (`chapter_prereading_schemas.py`)
- Register router in main app

### 5. Frontend - API Integration
- Generate API client from updated OpenAPI spec
- Rename `AISummaryIcon` to `AIIcon` in `theme/Icons.tsx`

### 6. Frontend - Components
- Create `StructureTab` component
- Create `ChapterAccordion` component
- Create `PrereadingContent` component
- Add "Structure" tab to `BookPage`
- Update route configuration if needed

### 7. Testing & Polish
- Write backend unit tests
- Write backend integration tests
- Write frontend component tests
- Manual testing with real EPUBs
- UI polish and mobile testing

## Future Enhancements (Out of Scope)

- **Regenerate button** - Allow users to regenerate existing content with different AI model
- **Bulk generation** - "Generate all" button to create prereading for entire book
- **Export** - Export book structure with prereading content as PDF/markdown
- **Reading progress integration** - Show which chapters user has read vs. not read
- **Estimated reading time** - Calculate based on chapter word count and average reading speed
- **Chapter notes** - Allow users to add their own notes alongside AI-generated content

## Open Questions

None - design is complete and approved.

## References

- Existing EPUB text extraction: `backend/src/application/library/services/ebook_text_extraction_service.py`
- Existing AI agents: `backend/src/infrastructure/ai/ai_agents.py`
- Existing book page: `frontend/src/pages/BookPage/BookPage.tsx`
- Domain architecture: `CLAUDE.md`
