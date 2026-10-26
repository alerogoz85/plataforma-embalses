import { describe, expect, it } from "vitest";

import { codigo, enLista, fechaIso, mesIso, textoLibre } from "@/lib/utils/url";

describe("enLista", () => {
  it("acepta solo los valores de la lista y devuelve el valor tipado (numero o texto)", () => {
    const periodos = enLista([12, 36, 60, 0] as const);
    expect(periodos("12")).toBe(12);
    expect(periodos("0")).toBe(0);
    expect(periodos("7")).toBeUndefined();
    expect(periodos("")).toBeUndefined();
    expect(periodos("12; DROP TABLE x")).toBeUndefined();
    expect(enLista(["asc", "desc"] as const)("desc")).toBe("desc");
    expect(enLista(["asc", "desc"] as const)("DESC")).toBeUndefined();
  });
});

describe("fechaIso", () => {
  it.each([["2026-10-26", "2026-10-26"], ["2026-02-29", undefined], ["2024-02-29", "2024-02-29"], ["26-10-2026", undefined], ["2026-13-01", undefined], ["hoy", undefined], ["2026-10-26T10:00", undefined]])(
    "%s", (crudo, esperado) => expect(fechaIso(crudo)).toBe(esperado),
  );
});

describe("mesIso", () => {
  it.each([["2026-10", "2026-10"], ["2026-00", undefined], ["2026-13", undefined], ["2026-1", undefined], ["2026-10-01", undefined]])("%s", (crudo, esperado) => expect(mesIso(crudo)).toBe(esperado));
});

describe("codigo", () => {
  const lector = codigo(10);
  it("acepta letras con tilde, numeros, espacios, guion y guion bajo", () => {
    expect(lector("Are0018")).toBe("Are0018");
    expect(codigo(20)("Eje Cafetero")).toBe("Eje Cafetero");
    expect(codigo(20)("Río_Grande-2")).toBe("Río_Grande-2");
  });
  it("rechaza marcado, comillas, rutas, controles y largos excesivos", () => {
    for (const malo of ["<script>", "a'b", "../etc", "a;b", "a\nb", "", "a".repeat(11), "x=1&y=2"]) expect(lector(malo)).toBeUndefined();
  });
});

describe("textoLibre", () => {
  it("recorta, quita caracteres de control y limita el largo; vacio es ausente", () => {
    const lector = textoLibre(5);
    expect(lector("  guavio  ")).toBe("guavi");
    expect(lector("a\u0000b\u001fc")).toBe("abc");
    expect(lector("   ")).toBeUndefined();
    expect(lector("")).toBeUndefined();
  });
});
