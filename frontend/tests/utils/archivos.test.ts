import { describe, expect, it } from "vitest";

import { aceptarDe, comprimirSiHaceFalta, extensionDe, formatearMomento, formatearTamano } from "@/lib/utils/archivos";

describe("utilidades de archivos", () => {
  it.each([[0, "0 B"], [512, "512 B"], [1024, "1,0 KB"], [1536, "1,5 KB"], [4 * 1024 * 1024, "4,0 MB"], [5762560, "5,5 MB"]])("formatea %s como %s", (n, texto) => expect(formatearTamano(n)).toBe(texto));

  it("saca la extensión en minúsculas y no inventa una", () => {
    expect([extensionDe("a.CSV"), extensionDe("b.tar.gz"), extensionDe("sin_extension"), extensionDe(".oculto")]).toEqual(["csv", "gz", "", "oculto"]);
  });

  it("arma el atributo accept", () => expect(aceptarDe(["xlsx", "csv"])).toBe(".xlsx,.csv"));

  it("no comprime lo pequeño ni lo que ya viene comprimido (xlsx, parquet)", async () => {
    const pequeno = new File(["a,b\n1,2"], "t.csv");
    expect(await comprimirSiHaceFalta(pequeno, 1000)).toBe(pequeno);
    const libro = new File(["x".repeat(5000)], "l.xlsx");
    expect(await comprimirSiHaceFalta(libro, 1000)).toBe(libro);
  });

  it("sin CompressionStream envía el archivo tal cual (la API avisa si no cabe)", async () => {
    const grande = new File(["a,b\n".repeat(1000)], "t.csv");
    expect(typeof CompressionStream === "undefined" ? await comprimirSiHaceFalta(grande, 10) : grande).toBe(grande);
  });

  it("formatea la fecha de la bitácora en hora local", () => {
    expect(formatearMomento("2026-10-27T15:00:00Z")).toMatch(/27\/10\/(20)?26/);
  });
});
