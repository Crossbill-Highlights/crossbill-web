import { DialogTabs } from "crossbill-frontend";

const panel = (text: string) => (
  <div
    style={{
      padding: "4px 8px",
      fontFamily: '"Lora", Georgia, serif',
      fontSize: 15,
      color: "#2E2215",
      lineHeight: 1.6,
    }}
  >
    {text}
  </div>
);

const tabs = [
  {
    key: "highlights",
    label: "Highlights",
    count: 12,
    content: panel("Twelve highlights captured while reading this chapter."),
  },
  {
    key: "notes",
    label: "Notes",
    count: 3,
    content: panel("Three notes — your thoughts and questions on the text."),
  },
  {
    key: "flashcards",
    label: "Flashcards",
    content: panel("No flashcards yet. Generate some from your highlights."),
  },
];

export const Default = () => (
  <div style={{ width: 460 }}>
    <DialogTabs tabs={tabs} />
  </div>
);

export const WithCounts = () => (
  <div style={{ width: 460 }}>
    <DialogTabs
      tabs={[
        {
          key: "all",
          label: "All",
          count: 24,
          content: panel("Everything in this chapter."),
        },
        {
          key: "bookmarked",
          label: "Bookmarked",
          count: 5,
          content: panel("Your five bookmarked items."),
        },
      ]}
    />
  </div>
);
