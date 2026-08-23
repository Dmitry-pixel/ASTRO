/** Сборка CSS для админ-панели. Заменяет рантайм cdn.tailwindcss.com. */
module.exports = {
  content: ["./src/humandesign/templates/**/*.html"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Outfit', 'sans-serif'],
      },
    },
  },
}
