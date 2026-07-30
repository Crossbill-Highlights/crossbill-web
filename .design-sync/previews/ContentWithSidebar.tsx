import { ContentWithSidebar } from "crossbill-frontend";

const panel = (heading: string, body: string, muted?: boolean) => (
  <div
    style={{
      border: "1px solid #e7e5e4",
      borderRadius: 8,
      padding: 16,
      background: muted ? "#fafaf9" : "#fff",
      fontFamily: '"Lora", Georgia, serif',
    }}
  >
    <strong style={{ color: "#43311E" }}>{heading}</strong>
    <div style={{ color: "#78716c", marginTop: 6, lineHeight: 1.6 }}>
      {body}
    </div>
  </div>
);

export const Default = () => (
  <ContentWithSidebar>
    {panel(
      "Main content",
      "The primary reading column — highlights, notes, and chapter text flow here.",
    )}
    {panel(
      "Sidebar (280px)",
      "Chapter list, filters, and metadata sit in the fixed-width sidebar.",
      true,
    )}
  </ContentWithSidebar>
);
