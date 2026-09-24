import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

function crearMatchMedia(coincide = false) {
  return (consulta: string): MediaQueryList =>
    ({
      matches: coincide,
      media: consulta,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList;
}

afterEach(() => {
  cleanup();
  window.matchMedia = crearMatchMedia();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.localStorage.clear();
  document.documentElement.classList.remove("dark");
});

window.matchMedia = crearMatchMedia();

// <style jsx> (usado en FiltersPanel) solo lo transforma el compilador de Next;
// fuera de Next React avisa por el atributo `jsx`. Se silencia ese aviso conocido.
const consoleError = console.error;
console.error = (...args: unknown[]) => {
  if (typeof args[0] === "string" && args[0].includes("non-boolean attribute")) return;
  consoleError(...args);
};
