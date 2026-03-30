import React, { useState } from "react";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { useLocation } from "@docusaurus/router";
import { RiLinkM } from "@remixicon/react";
import { ReportUrlDialog } from "../../../components/ReportUrlDialog";
import { useReport } from "../../../components/ReportProvider";

export default function NavbarLogo(): React.JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  const { pathname } = useLocation();
  const { report, loading } = useReport();
  const [copied, setCopied] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const req = report?.request ?? {};
  const fields = [
    { label: "Registry", value: req.registry, full: req.registry },
    { label: "Repository", value: req.repository, full: req.repository },
    { label: "Tag", value: req.tag, full: req.tag },
    {
      label: "Digest",
      value: req.digest ? req.digest.slice(0, 19) + "…" : undefined,
      full: req.digest,
    },
  ].filter((f) => f.value);

  // Hide report-specific metadata on the Archive (homepage)
  const isArchivePage =
    pathname === siteConfig.baseUrl || pathname === `${siteConfig.baseUrl}/`;

  function copy(label: string, full: string | undefined) {
    if (!full) return;
    navigator.clipboard.writeText(full).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(null), 1500);
    });
  }

  return (
    <>
      <Link to="/" className="navbar__brand">
        <b className="navbar__title">{siteConfig.title}</b>
      </Link>
      <button
        onClick={() => setDialogOpen(true)}
        className="navbar__item navbar__link inline-flex items-center gap-1"
        style={{
          marginLeft: "auto",
          flexShrink: 0,
          background: "none",
          border: "none",
          cursor: "pointer",
        }}
        title="Load report from URL"
      >
        <RiLinkM size={14} />
        Load URL
      </button>
      <ReportUrlDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
      {!loading && !isArchivePage && fields.length > 0 && (
        <div
          className="flex items-center gap-2"
          style={{
            position: "absolute",
            left: "50%",
            transform: "translateX(-50%)",
          }}
        >
          {fields.map((f) => (
            <span
              key={f.label}
              onClick={() => copy(f.label, f.full)}
              title={f.full}
              className="inline-flex items-center rounded overflow-hidden border border-gray-300 dark:border-gray-600 text-xs cursor-pointer select-none"
            >
              <span className="px-2 py-1 bg-gray-700 dark:bg-gray-200 text-white dark:text-gray-800 uppercase tracking-wider font-bold text-[0.65rem]">
                {f.label}
              </span>
              <span className="px-2 py-1 font-mono bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 transition-colors">
                {copied === f.label ? "✓ copied" : f.value}
              </span>
            </span>
          ))}
        </div>
      )}
    </>
  );
}
