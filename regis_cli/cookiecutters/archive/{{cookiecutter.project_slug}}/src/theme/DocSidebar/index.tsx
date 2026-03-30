import React, { type ReactNode } from "react";
import DocSidebar from "@theme-original/DocSidebar";
import type DocSidebarType from "@theme/DocSidebar";
import type { WrapperProps } from "@docusaurus/types";

import { useReport } from "@site/src/components/ReportProvider";
import { RiFileListLine } from "@remixicon/react";

type Props = WrapperProps<typeof DocSidebarType>;

export default function DocSidebarWrapper(props: Props): ReactNode {
  return (
    <>
      <DocSidebar {...props} />
    </>
  );
}
