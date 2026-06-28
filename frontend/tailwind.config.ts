import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        slate: "#334155",
        mist: "#f8fafc",
        signal: "#0f766e",
        alert: "#b45309",
      },
    },
  },
  plugins: [],
};

export default config;
