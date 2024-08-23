/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        "roboto-condensed": ['"Roboto Condensed"', "sans-serif"],
        assistant: ['"Assistant"', "sans-serif"],
      },
      backgroundColor: {
        "akvo-green-100": "#EBFEDE",
        "akvo-green": "#006349",
      },
      textColor: {
        "akvo-green": "#006349",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
