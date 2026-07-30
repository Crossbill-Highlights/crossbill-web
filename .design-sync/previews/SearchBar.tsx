import { SearchBar } from "crossbill-frontend";

const noop = () => {};

export const Empty = () => (
  <div style={{ width: 420 }}>
    <SearchBar onSearch={noop} placeholder="Search highlights…" />
  </div>
);

export const WithQuery = () => (
  <div style={{ width: 420 }}>
    <SearchBar
      onSearch={noop}
      placeholder="Search highlights…"
      initialValue="wonder"
    />
  </div>
);

export const SearchingBooks = () => (
  <div style={{ width: 420 }}>
    <SearchBar
      onSearch={noop}
      placeholder="Search your library…"
      initialValue="Moby-Dick"
    />
  </div>
);
