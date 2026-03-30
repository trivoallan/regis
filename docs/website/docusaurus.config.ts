import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: "regis-cli",
  tagline: "Container Security & Policy-as-Code Orchestration",
  markdown: {
    format: "detect",
    mermaid: true,
  },
  staticDirectories: ["static"],

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: false,
  },

  // Set the production url of your site here
  url: "https://trivoallan.github.io",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/regis-cli/docs/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "trivoallan", // Usually your GitHub org/user name.
  projectName: "regis-cli", // Usually your repo name.

  onBrokenLinks: "ignore", // versioned_docs are immutable; broken links in historical snapshots are acceptable
  onBrokenAnchors: "ignore", // Schema docs use <a name="..."> anchors not recognized by the checker

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  themes: [
    "@docusaurus/theme-mermaid",
    [
      "@easyops-cn/docusaurus-search-local",
      {
        hashed: true,
        docsRouteBasePath: "/",
        indexBlog: false,
      },
    ],
  ],

  presets: [
    [
      "classic",
      {
        docs: {
          routeBasePath: "/",
          versions: {
            current: {
              label: "main-dev",
              banner: "unreleased",
            },
          },
          editUrl:
            "https://github.com/trivoallan/regis-cli/edit/main/docs/website/",
        },
        blog: false,
        pages: false,
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: "light",
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: "Regis CLI",
      items: [
        {
          type: "docsVersionDropdown",
          position: "right",
          dropdownActiveClassDisabled: true,
        },
        {
          href: "https://github.com/trivoallan/regis-cli",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {},
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
