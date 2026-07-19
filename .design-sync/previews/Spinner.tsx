import { Spinner } from "crossbill-frontend";

export const Sizes = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
    <Spinner size={24} />
    <Spinner size={40} />
    <Spinner size={64} />
  </div>
);
