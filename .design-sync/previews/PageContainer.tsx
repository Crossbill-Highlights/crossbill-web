import { PageContainer } from "crossbill-frontend";

export const Default = () => (
  <PageContainer maxWidth="md">
    <div
      style={{
        border: "1px dashed #d6d3d1",
        borderRadius: 8,
        padding: 24,
        fontFamily: '"Lora", Georgia, serif',
      }}
    >
      <h2 style={{ margin: "0 0 8px", color: "#43311E" }}>Page content</h2>
      <p style={{ margin: 0, color: "#57534e", lineHeight: 1.6 }}>
        PageContainer centers page content and applies the app’s responsive top
        margin and generous bottom padding (leaving room for the mobile action
        bar and device safe-area insets).
      </p>
    </div>
  </PageContainer>
);
