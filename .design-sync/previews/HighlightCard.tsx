import { HighlightCard } from "crossbill-frontend";

const highlight = {
  id: 1,
  text: "The sea, once it casts its spell, holds one in its net of wonder forever.",
  datetime: "2024-06-12T10:00:00Z",
  page: 42,
  chapter_id: 1,
  book_id: 1,
  created_at: "2024-06-12T10:00:00Z",
  updated_at: "2024-06-12T10:00:00Z",
  label: { text: "Favorite", ui_color: "#685A4B" },
  tags: [
    { id: 1, name: "ocean" },
    { id: 2, name: "wonder" },
  ],
  flashcards: [{ id: 1 }, { id: 2 }],
};

export const Default = () => (
  <div style={{ width: 560 }}>
    <HighlightCard highlight={highlight} onOpenModal={() => {}} />
  </div>
);

export const Bookmarked = () => (
  <div style={{ width: 560 }}>
    <HighlightCard
      highlight={highlight}
      bookmark={{ id: 1 }}
      onOpenModal={() => {}}
    />
  </div>
);
