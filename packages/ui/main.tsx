import React from "react";
import { createRoot } from "react-dom/client";
import { ReportApp } from "./ReportApp";
import "@regis-cli/ui/theme";

const root = document.getElementById("root");
if (!root) throw new Error("Missing #root element");

createRoot(root).render(
  <React.StrictMode>
    <ReportApp />
  </React.StrictMode>,
);
