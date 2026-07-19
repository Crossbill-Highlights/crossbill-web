import { AIActionButton } from "crossbill-frontend";

const noop = () => {};

export const GenerateFlashcards = () => (
  <AIActionButton text="Generate flashcards" onClick={noop} />
);

export const Disabled = () => (
  <AIActionButton text="Generate summary" onClick={noop} disabled />
);

export const InsideAHighlight = () => (
  <div
    style={{
      width: 420,
      padding: "14px 16px",
      border: "1px solid #e7e5e4",
      borderRadius: 8,
      fontFamily: '"Lora", Georgia, serif',
      color: "#43311E",
    }}
  >
    <div style={{ fontSize: 15, lineHeight: 1.5, marginBottom: 10 }}>
      “The sea, once it casts its spell, holds one in its net of wonder
      forever.”
    </div>
    <AIActionButton text="Explain this highlight" onClick={noop} />
  </div>
);
