import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        masuite: {
          50: "#eff6ff",
          100: "#dbeafe",
          600: "#000091",
          700: "#00006d",
          800: "#000058",
          900: "#0a0a2e",
        },
      },
    },
  },
  plugins: [],
};

export default config;
