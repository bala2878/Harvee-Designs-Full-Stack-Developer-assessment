/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        accent: { DEFAULT: "#6366F1", hover: "#4F46E5", light: "#EEF2FF" },
        navy: { DEFAULT: "#0B0E1A", light: "#151A2E" },
        status: {
          success: { bg: "#DCFCE7", text: "#166534" },
          error: { bg: "#FEE2E2", text: "#991B1B" },
        },
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      borderRadius: { card: "12px" },
    },
  },
  plugins: [],
};
