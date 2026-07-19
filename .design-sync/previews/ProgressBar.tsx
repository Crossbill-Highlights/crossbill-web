import { ProgressBar } from "crossbill-frontend";

const row = (label: string, currentIndex: number, totalCount: number) => (
  <div style={{ marginBottom: 18 }}>
    <div
      style={{
        fontFamily: '"Lora", Georgia, serif',
        fontSize: 13,
        color: "#78716c",
        marginBottom: 6,
      }}
    >
      {label}
    </div>
    <ProgressBar currentIndex={currentIndex} totalCount={totalCount} />
  </div>
);

export const FlashcardSteps = () => (
  <div style={{ width: "100%", maxWidth: 520 }}>
    {row("Card 1 of 8", 0, 8)}
    {row("Card 4 of 8", 3, 8)}
    {row("Card 8 of 8", 7, 8)}
  </div>
);
