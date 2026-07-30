import { HoverableCardActionArea, MetadataRow } from "crossbill-frontend";

export const BookRow = () => (
  <div style={{ width: 460 }}>
    <HoverableCardActionArea sx={{ p: 2 }}>
      <div
        style={{
          fontFamily: '"Lora", Georgia, serif',
          fontSize: 17,
          fontWeight: 600,
          color: "#43311E",
          marginBottom: 4,
        }}
      >
        Moby-Dick; or, The Whale
      </div>
      <MetadataRow items={["Herman Melville", "1851", "135 chapters"]} />
    </HoverableCardActionArea>
  </div>
);

export const ChapterRow = () => (
  <div style={{ width: 460 }}>
    <HoverableCardActionArea sx={{ p: 2 }}>
      <div
        style={{
          fontFamily: '"Lora", Georgia, serif',
          fontSize: 15,
          color: "#43311E",
        }}
      >
        Chapter 3 — “The Spouter-Inn”
      </div>
      <MetadataRow items={["8 highlights", "2 notes"]} />
    </HoverableCardActionArea>
  </div>
);
