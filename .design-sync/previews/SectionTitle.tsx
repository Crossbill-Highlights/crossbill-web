import { SectionTitle } from "crossbill-frontend";

export const Default = () => <SectionTitle>Highlights</SectionTitle>;

export const WithDivider = () => (
  <SectionTitle showDivider>Reading progress</SectionTitle>
);

export const HeadingLevels = () => (
  <div
    style={{ display: "flex", flexDirection: "column", gap: 12, width: 360 }}
  >
    <SectionTitle component="h1">Book overview</SectionTitle>
    <SectionTitle component="h2" showDivider>
      Chapters
    </SectionTitle>
    <SectionTitle component="h3">Notes &amp; flashcards</SectionTitle>
  </div>
);
