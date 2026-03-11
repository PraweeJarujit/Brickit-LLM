/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // <--- เพิ่มบรรทัดนี้เข้ามาครับ เพื่อให้ใช้ปุ่ม Toggle ได้
  content: [
    "./index.html",
    "./ai-studio.html",
    "./ai-studio-mobile.html", 
    "./ai-studio-fixed.html",
    "./ai-studio-enhanced.html",
    "./login.html",
    "./checkout.html",
    "./size-s.html",
    "./size-m.html",
    "./size-l.html",
    "./orders.html",
    "./admin.html",
    "./code.html",
    "./responsive_frontend.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#19e619",
        "text-main": "#1f2937",
        "text-light": "#6b7280",
        "surface-light": "#ffffff",
        "surface-dark": "#1f2937",
        "background-light": "#f9fafb",
        "background-dark": "#111827",
        "accent-green-light": "#f0fdf4",
        "accent-green-dark": "#064e3b",
        "border-light": "#e5e7eb",
        "border-dark": "#374151"
      },
      fontFamily: {
        "display": ["Spline Sans", "Noto Sans Thai", "sans-serif"]
      },
      animation: {
        "img-interactive-fade": "imgInteractiveFade 0.6s ease-in-out"
      },
      keyframes: {
        imgInteractiveFade: {
          "0%": { opacity: "0.7", transform: "scale(0.98)" },
          "100%": { opacity: "1", transform: "scale(1)" }
        }
      }
    },
  },
  plugins: [],
}