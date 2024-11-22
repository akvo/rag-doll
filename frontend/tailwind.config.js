/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        "roboto-condensed": ['"Roboto Condensed"', "sans-serif"],
        assistant: ['"Assistant"', "sans-serif"],
      },
      colors: {
        "akvo-green-100": "#EBFEDE",
      },
      backgroundColor: {
        "akvo-green-100": "#EBFEDE",
        "akvo-green": "#006349",
      },
      textColor: {
        "akvo-green-100": "#EBFEDE",
        "akvo-green": "#006349",
      },
      ringColor: {
        "akvo-green": "#006349",
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: "100%", // Remove prose default max-width
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
