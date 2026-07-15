"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const root = document.documentElement;
    const saved = window.localStorage.getItem("bz-theme");
    const initial: Theme = saved === "light" || saved === "dark"
      ? saved
      : window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";

    const frame = window.requestAnimationFrame(() => setTheme(initial));
    root.dataset.theme = initial;
    root.style.colorScheme = initial;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const syncWithSystem = (event: MediaQueryListEvent) => {
      if (window.localStorage.getItem("bz-theme")) return;
      const nextTheme: Theme = event.matches ? "dark" : "light";
      setTheme(nextTheme);
      root.dataset.theme = nextTheme;
      root.style.colorScheme = nextTheme;
    };

    media.addEventListener("change", syncWithSystem);
    return () => {
      window.cancelAnimationFrame(frame);
      media.removeEventListener("change", syncWithSystem);
    };
  }, []);

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
    document.documentElement.style.colorScheme = nextTheme;
    window.localStorage.setItem("bz-theme", nextTheme);
  }

  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      aria-pressed={theme === "dark"}
    >
      <span className="theme-icon" aria-hidden="true"><i /></span>
      <span>{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
