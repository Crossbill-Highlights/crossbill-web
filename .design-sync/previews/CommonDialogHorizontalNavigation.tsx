import { CommonDialogHorizontalNavigation } from "crossbill-frontend";

const body = (
  <div
    style={{
      fontFamily: '"Lora", Georgia, serif',
      fontSize: 15,
      lineHeight: 1.6,
      color: "#2E2215",
    }}
  >
    <strong style={{ color: "#43311E" }}>Highlight 3 of 12</strong>
    <p style={{ margin: "8px 0 0" }}>
      “The sea, once it casts its spell, holds one in its net of wonder
      forever.”
    </p>
  </div>
);

export const Middle = () => (
  <CommonDialogHorizontalNavigation
    hasNavigation
    hasPrevious
    hasNext
    onPrevious={() => {}}
    onNext={() => {}}
  >
    {body}
  </CommonDialogHorizontalNavigation>
);

export const AtStart = () => (
  <CommonDialogHorizontalNavigation
    hasNavigation
    hasPrevious={false}
    hasNext
    onPrevious={() => {}}
    onNext={() => {}}
  >
    {body}
  </CommonDialogHorizontalNavigation>
);
