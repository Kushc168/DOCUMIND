/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        electric: "#3b82f6",
        panel: "rgba(255,255,255,0.06)",
        panelBorder: "rgba(255,255,255,0.12)",
      },
      boxShadow: {
        glow: "0 0 30px rgba(59, 130, 246, 0.25)",
        glass: "0 16px 40px rgba(2,6,23,0.45)",
      },
      backdropBlur: {
        glass: "12px",
      },
      fontFamily: {
        sans: ["Inter", "Geist", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
