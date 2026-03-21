import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";
import { createRequire } from "module";

const require = createRequire(import.meta.url);

const config: Config = {
  title: "{{ cookiecutter.project_name }}",
  tagline: "{{ cookiecutter.description }}",
  favicon: "img/favicon.ico",

  url: process.env.ARCHIVE_URL || "http://localhost",
  baseUrl: process.env.ARCHIVE_BASE_URL || "/",

  onBrokenLinks: "warn",

  i18n: { defaultLocale: "en", locales: ["en"] },

  presets: [
    [
      "classic",
      {
        docs: {
          routeBasePath: "/",
          sidebarItemsGenerator: async () => [
            { type: "doc", id: "index", label: "Archive" },
          ],
        },
        blog: false,
        pages: false,
        theme: { customCss: "./src/css/custom.css" },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    async function tailwindPlugin(context, options) {
      return {
        name: "docusaurus-tailwindcss",
        configurePostCss(postcssOptions) {
          postcssOptions.plugins.push(require("tailwindcss"));
          postcssOptions.plugins.push(require("autoprefixer"));
          return postcssOptions;
        },
      };
    },
  ],

  themeConfig: {
    colorMode: { defaultMode: "dark", respectPrefersColorScheme: true },
    navbar: {
      title: "{{ cookiecutter.project_name }}",
      items: [],
    },
    footer: {
      style: "dark",
      copyright: `Powered by <a href="https://github.com/trivoallan/regis-cli">regis-cli</a>`,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
