/** @type {import('tailwindcss').Config} */
module.exports = {
  corePlugins: { preflight: false },
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./docs/**/*.{md,mdx}",
    "./node_modules/@tremor/react/dist/*.{js,cjs}",
  ],
  theme: { extend: {} },
  plugins: [],
};
