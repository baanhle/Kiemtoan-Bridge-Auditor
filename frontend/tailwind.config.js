/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "primary": "#004e58",
        "primary-container": "#006875",
        "primary-fixed": "#a2effe",
        "on-primary": "#ffffff",
        "surface": "#f8fafb",
        "on-surface": "#191c1d",
        "surface-container-low": "#f2f4f5",
        "surface-container-high": "#e6e8e9",
        "surface-container-highest": "#e1e3e4",
        "outline": "#6f797b",
        "outline-variant": "#bec8cb",
        "error": "#ba1a1a",
        "error-container": "#ffdad6",
      },
      fontFamily: {
        "headline": ["Space Grotesk", "sans-serif"],
        "body": ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
}
