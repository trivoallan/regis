import React, { type ReactNode } from "react";
import Content from "@theme-original/DocSidebar/Desktop/Content";
import type ContentType from "@theme/DocSidebar/Desktop/Content";
import type { WrapperProps } from "@docusaurus/types";

import { useReport } from "@site/src/components/ReportProvider";
import { RiFileListLine } from "@remixicon/react";

type Props = WrapperProps<typeof ContentType>;

export default function ContentWrapper(props: Props): ReactNode {
  const { reportUrl } = useReport();

  return (
    <>
      <Content {...props} />
      {reportUrl && (
        <ul className="menu__list mt-4 border-t border-gray-200 dark:border-gray-800 pt-4 px-2">
          <li className="menu__list-item">
            <a
              href={reportUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="menu__link flex items-center justify-center gap-2 font-medium"
              style={{
                fontSize: "0.8rem",
                color: "var(--ifm-color-primary)",
              }}
            >
              <RiFileListLine size={14} />
              Raw JSON Report
            </a>
          </li>
        </ul>
      )}
    </>
  );
}
