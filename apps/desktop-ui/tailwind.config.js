/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aegis: {
          900: "#090d16",
          800: "#0f172a",
          700: "#1e293b",
          600: "#334155",
          accent: "#38bdf8",
          glow: "#0284c7",
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444",
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        pulseFast: "pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        wave: "wave 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
}
