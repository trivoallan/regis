import React from "react";
import Layout from "@theme/Layout";
import { ArchiveView } from "@site/src/components/ArchiveView";

export default function ArchivePage(): React.JSX.Element {
  return (
    <Layout title="Archive">
      <ArchiveView />
    </Layout>
  );
}
