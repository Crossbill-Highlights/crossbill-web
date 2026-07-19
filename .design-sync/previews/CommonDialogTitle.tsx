import { CommonDialogTitle } from "crossbill-frontend";

export const Default = () => (
  <CommonDialogTitle>Highlight details</CommonDialogTitle>
);

export const LongTitleTruncates = () => (
  <div
    style={{
      width: 320,
      border: "1px solid #e7e5e4",
      borderRadius: 8,
      padding: "10px 14px",
    }}
  >
    <CommonDialogTitle>
      The Old Man and the Sea — Chapter 3: “The Marlin and the Long Vigil”
    </CommonDialogTitle>
  </div>
);

export const InDialogHeader = () => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      width: 420,
      padding: "12px 16px",
      borderBottom: "1px solid #e7e5e4",
      background: "#fff",
    }}
  >
    <CommonDialogTitle>Edit flashcard</CommonDialogTitle>
    <span
      style={{
        fontFamily: '"Lora", Georgia, serif',
        fontSize: 13,
        color: "#78716c",
      }}
    >
      Deck: Marine biology
    </span>
  </div>
);
