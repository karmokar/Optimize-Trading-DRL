import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))", // Fixes the current error
        foreground: "hsl(var(--foreground))", // Prevents the next likely error
      },
    },
  },
  plugins: [],
};

export default config;