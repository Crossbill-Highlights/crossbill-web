import { TagInput } from "crossbill-frontend";

const available = [
  { id: 1, name: "ocean" },
  { id: 2, name: "philosophy" },
  { id: 3, name: "memory" },
  { id: 4, name: "wonder" },
];

const selected = [
  { id: 1, name: "ocean" },
  { id: 2, name: "philosophy" },
];

export const Default = () => (
  <div style={{ width: 420 }}>
    <TagInput value={selected} onChange={() => {}} availableTags={available} />
  </div>
);

export const Empty = () => (
  <div style={{ width: 420 }}>
    <TagInput value={[]} onChange={() => {}} availableTags={available} />
  </div>
);

export const Disabled = () => (
  <div style={{ width: 420 }}>
    <TagInput value={selected} onChange={() => {}} disabled />
  </div>
);
