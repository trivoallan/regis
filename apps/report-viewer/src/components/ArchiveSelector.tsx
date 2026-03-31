import React from "react";
import { Tab, TabGroup, TabList } from "@tremor/react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ArchiveDef {
  name: string;
  path: string;
}

interface Props {
  archives: ArchiveDef[];
  activeIndex: number; // -1 = "All Archives" combined view
  onSelect: (idx: number) => void;
}

// ---------------------------------------------------------------------------
// ArchiveSelector
// ---------------------------------------------------------------------------

export function ArchiveSelector({
  archives,
  activeIndex,
  onSelect,
}: Props): React.JSX.Element {
  // Map activeIndex (-1 → 0, 0 → 1, 1 → 2, …) to TabGroup index
  const tabIndex = activeIndex + 1;

  function handleChange(idx: number) {
    // Map TabGroup index back to activeIndex (0 → -1, 1 → 0, …)
    onSelect(idx - 1);
  }

  const tabs: React.ReactElement[] = [
    <Tab key="__all__">All Archives</Tab>,
    ...archives.map((a) => <Tab key={a.path}>{a.name}</Tab>),
  ];

  return (
    <TabGroup index={tabIndex} onIndexChange={handleChange}>
      <TabList>{tabs}</TabList>
    </TabGroup>
  );
}
