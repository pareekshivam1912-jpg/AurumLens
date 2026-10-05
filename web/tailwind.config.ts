import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: "#B7862C",
          hover: "#9A6F22",
          tint: "#FBF3E0",
          border: "#EAD7B2",
        },
        ink: "#1E1E1E",
        slate: {
          DEFAULT: "#4B5563",
          light: "#9CA3AF",
        },
        panel: {
          DEFAULT: "#F7F5F0",
          darker: "#EFECE6",
        },
        quiet: {
          DEFAULT: "#2E7D32",
          bg: "#E8F5E9",
          border: "#A5D6A7",
        },
        alert: {
          DEFAULT: "#C62828",
          bg: "#FFEBEE",
          border: "#FFCDD2",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
