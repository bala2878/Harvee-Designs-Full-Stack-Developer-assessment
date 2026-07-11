/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: "#6366F1", // indigo — primary action color
          hover: "#4F46E5",
          light: "#EEF2FF",
        },
        navy: {
          DEFAULT: "#0B0E1A", // sidebar background
          light: "#151A2E",
        },
        status: {
          allocated: { bg: "#DCFCE7", text: "#166534" },
          pending: { bg: "#FEF3C7", text: "#92400E" },
          rejected: { bg: "#FEE2E2", text: "#991B1B" },
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "12px",
      },
    },
  },
  plugins: [],
};
