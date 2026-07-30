import { Collapsable } from "crossbill-frontend";

export const ExpandedNote = () => (
  <div style={{ width: 340 }}>
    <div
      style={{
        fontFamily: '"Lora", Georgia, serif',
        fontSize: 13,
        fontWeight: 600,
        color: "#78716c",
        marginBottom: 6,
      }}
    >
      Chapter 3 · Notes
    </div>
    <Collapsable isExpanded>
      <div
        style={{
          fontFamily: '"Lora", Georgia, serif',
          fontSize: 14,
          lineHeight: 1.6,
          color: "#43311E",
          padding: "10px 14px",
          border: "1px solid #e7e5e4",
          borderRadius: 8,
        }}
      >
        The marlin represents both the old man’s greatest triumph and the
        futility of his struggle against nature.
      </div>
    </Collapsable>
  </div>
);

export const ExpandedFlashcards = () => (
  <div style={{ width: 340 }}>
    <Collapsable isExpanded>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {["What does the marlin symbolize?", "Who accompanies Santiago?"].map(
          (q) => (
            <div
              key={q}
              style={{
                fontFamily: '"Lora", Georgia, serif',
                fontSize: 14,
                color: "#43311E",
                padding: "10px 14px",
                background: "#faf8f5",
                border: "1px solid #e7e5e4",
                borderRadius: 8,
              }}
            >
              {q}
            </div>
          ),
        )}
      </div>
    </Collapsable>
  </div>
);
