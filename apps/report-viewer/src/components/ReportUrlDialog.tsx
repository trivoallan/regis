/**
 * ReportUrlDialog — modal dialog to load a report from a custom URL.
 *
 * On submit, navigates to the current page with `?report=<url>`, which
 * Root.tsx picks up to pass a new URL to ReportProvider.
 */

import React, { useEffect, useState } from "react";
import { Dialog, DialogPanel, DialogTitle } from "@headlessui/react";

interface ReportUrlDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ReportUrlDialog({
  isOpen,
  onClose,
}: ReportUrlDialogProps): React.JSX.Element {
  const [url, setUrl] = useState("");

  useEffect(() => {
    if (isOpen) {
      setUrl(new URLSearchParams(window.location.search).get("report") ?? "");
    }
  }, [isOpen]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = url.trim();
    const search = trimmed ? `?report=${encodeURIComponent(trimmed)}` : "";
    window.location.href = window.location.pathname + search;
  }

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm"
        aria-hidden="true"
      />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel className="w-full max-w-lg rounded-xl bg-white dark:bg-gray-900 p-6 shadow-2xl border border-gray-200 dark:border-gray-700">
          <DialogTitle className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Load report from URL
          </DialogTitle>
          <form onSubmit={handleSubmit}>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/report.json"
              autoFocus
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors cursor-pointer"
              >
                Load
              </button>
            </div>
          </form>
        </DialogPanel>
      </div>
    </Dialog>
  );
}
