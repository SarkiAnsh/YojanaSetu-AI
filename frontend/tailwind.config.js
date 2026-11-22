/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors inspired by Indian tricolor
        saffron: {
          50:  '#fff7ed',
          100: '#ffedd5',
          500: '#FF9933',  // Indian saffron
          600: '#ea8020',
          700: '#c06010',
        },
        india: {
          green: '#138808',  // Indian green
          blue:  '#000080',  // Ashoka Chakra blue
        }
      },
      fontFamily: {
        // Noto Sans supports Devanagari (Hindi) script
        hindi: ['Noto Sans Devanagari', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
