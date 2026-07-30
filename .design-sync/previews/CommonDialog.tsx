import { CommonDialog, CommonDialogTitle } from "crossbill-frontend";

const footerBtn = (label: string, primary?: boolean) => (
  <button
    style={{
      fontFamily: '"Lora", Georgia, serif',
      fontSize: 14,
      fontWeight: 600,
      padding: "6px 16px",
      borderRadius: 6,
      cursor: "pointer",
      border: primary ? "none" : "1px solid transparent",
      color: primary ? "#fff" : "#685A4B",
      background: primary ? "#43311E" : "transparent",
    }}
  >
    {label}
  </button>
);

export const Default = () => (
  <CommonDialog
    open
    onClose={() => {}}
    maxWidth="sm"
    title={<CommonDialogTitle>Highlight details</CommonDialogTitle>}
    footerActions={
      <>
        {footerBtn("Cancel")}
        {footerBtn("Save", true)}
      </>
    }
  >
    <div
      style={{
        fontFamily: '"Lora", Georgia, serif',
        fontSize: 15,
        lineHeight: 1.7,
        color: "#2E2215",
      }}
    >
      <p style={{ margin: "0 0 12px" }}>
        “The sea, once it casts its spell, holds one in its net of wonder
        forever.”
      </p>
      <p style={{ margin: 0, color: "#78716c", fontSize: 13 }}>
        Chapter 3 · Page 42 · June 12, 2024
      </p>
    </div>
  </CommonDialog>
);
