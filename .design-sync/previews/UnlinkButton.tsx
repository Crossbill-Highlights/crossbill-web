import { UnlinkButton } from "crossbill-frontend";

const noop = () => {};

export const Default = () => (
  <UnlinkButton title="Unlink highlight" onClick={noop} />
);

export const Disabled = () => (
  <UnlinkButton title="Unlink highlight" onClick={noop} disabled />
);

export const InsideARow = () => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      width: 320,
      padding: "8px 14px",
      border: "1px solid #e7e5e4",
      borderRadius: 8,
      fontFamily: '"Lora", Georgia, serif',
      fontSize: 14,
      color: "#43311E",
    }}
  >
    <span>Chapter 3 — “The Tide Turns”</span>
    <UnlinkButton title="Unlink from chapter" onClick={noop} />
  </div>
);
