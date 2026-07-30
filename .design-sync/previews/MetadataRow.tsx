import { MetadataRow } from "crossbill-frontend";

export const BookMeta = () => (
  <div style={{ width: 460 }}>
    <MetadataRow items={["Herman Melville", "1851", "135 chapters"]} />
  </div>
);

export const HighlightMeta = () => (
  <div style={{ width: 460 }}>
    <MetadataRow
      items={["Chapter 42 — The Whiteness of the Whale", "Page 189", "3 tags"]}
    />
  </div>
);

export const WithDroppedItems = () => (
  <div style={{ width: 460 }}>
    <MetadataRow items={["12 highlights", null, "4 flashcards", false, ""]} />
  </div>
);
