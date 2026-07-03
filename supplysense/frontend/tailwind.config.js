/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#070B14",
          900: "#0B1120",
          800: "#121A2B",
          700: "#1B2538",
          600: "#27334A",
          500: "#3A4A66",
        },
        mist: {
          400: "#8B97AD",
          300: "#A9B4C7",
          200: "#C9D2E0",
          100: "#E7ECF4",
        },
        signal: {
          amber: "#FF8A3D",
          amberDim: "#7A4A26",
          teal: "#2DD4BF",
          tealDim: "#1B5F58",
          rose: "#FB5C72",
          roseDim: "#6B2530",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 12px 32px -16px rgba(0,0,0,0.6)",
        glowAmber: "0 0 0 1px rgba(255,138,61,0.3), 0 0 24px -4px rgba(255,138,61,0.4)",
        glowTeal: "0 0 0 1px rgba(45,212,191,0.3), 0 0 24px -4px rgba(45,212,191,0.4)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "28px 28px",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: 1, transform: "scale(1)" },
          "50%": { opacity: 0.4, transform: "scale(0.85)" },
        },
        flow: {
          "0%": { strokeDashoffset: "24" },
          "100%": { strokeDashoffset: "0" },
        },
        rise: {
          "0%": { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: {
        pulseDot: "pulseDot 2.2s ease-in-out infinite",
        flow: "flow 1.2s linear infinite",
        rise: "rise 0.35s ease-out",
      },
    },
  },
  plugins: [],
};
