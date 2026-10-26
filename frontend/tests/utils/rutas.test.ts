import { describe, expect, it } from "vitest";

import nextConfig from "../../next.config";
import {
  ALIAS_DE_RUTAS, ANCLAS_GUIA, IDS_TABLERO, RUTAS, conParametros, esRutaConocida, resolverRuta, rutaDe, urlGuia,
} from "@/lib/rutas";

describe("RUTAS", () => {
  it("las rutas canonicas empiezan con / y no terminan en / (salvo la raiz)", () => {
    for (const r of Object.values(RUTAS)) expect(r === "/" || (r.startsWith("/") && !r.endsWith("/"))).toBe(true);
  });

  it("hay una ruta por tablero y todas son distintas", () => {
    expect(IDS_TABLERO.map(rutaDe)).toEqual(["/embalses", "/carbon", "/dns", "/gas", "/optimizacion", "/apagon"]);
    expect(new Set(Object.values(RUTAS)).size).toBe(Object.keys(RUTAS).length);
  });

  it("cada tablero tiene un capitulo en la guia y urlGuia lo compone", () => {
    expect(Object.keys(ANCLAS_GUIA).sort()).toEqual([...IDS_TABLERO, "panel"].sort());
    expect(urlGuia("dns")).toBe("/informacion#dns-mapa");
    expect(urlGuia("panel")).toBe("/informacion#panel");
  });
});

describe("conParametros", () => {
  it("omite valores nulos, indefinidos y vacios y ordena las claves", () => {
    expect(conParametros("/dns", { region: "Caribe", periodo: 12, origen: null, subarea: undefined, q: "" })).toBe("/dns?periodo=12&region=Caribe");
  });

  it("sin parametros devuelve la ruta sola", () => {
    expect(conParametros("/dns", {})).toBe("/dns");
    expect(conParametros("/dns", { a: null })).toBe("/dns");
  });

  it("codifica caracteres especiales y conserva el cero y false", () => {
    expect(conParametros("/dns", { q: "a b&c", periodo: 0, activo: false })).toBe("/dns?activo=false&periodo=0&q=a+b%26c");
  });
});

describe("esRutaConocida y resolverRuta", () => {
  it.each([["/dns", true], ["/dns/", true], ["/dns?periodo=12", true], ["/dns#x", true], ["/", true], ["/otra", false], ["/dns/extra", false]])(
    "esRutaConocida(%s) = %s", (ruta, esperado) => expect(esRutaConocida(ruta)).toBe(esperado),
  );

  it("resuelve alias, mayusculas y barra final a la ruta canonica", () => {
    expect(resolverRuta("/Demanda-No-Atendida")).toBe("/dns");
    expect(resolverRuta("/tableros/")).toBe("/");
    expect(resolverRuta("/riesgo-apagon?x=1")).toBe("/apagon");
    expect(resolverRuta("/EMBALSES")).toBe("/embalses");
  });

  it("una direccion desconocida no se resuelve", () => {
    expect(resolverRuta("/nada")).toBeNull();
  });

  it("todo alias apunta a una ruta canonica y ningun alias pisa una ruta real", () => {
    for (const [alias, destino] of Object.entries(ALIAS_DE_RUTAS)) {
      expect(esRutaConocida(destino)).toBe(true);
      expect(esRutaConocida(alias)).toBe(false);
    }
  });
});

describe("next.config: redirecciones y reescrituras", () => {
  it("cada alias redirige a su ruta canonica", async () => {
    const redirecciones = await nextConfig.redirects!();
    expect(redirecciones).toHaveLength(Object.keys(ALIAS_DE_RUTAS).length);
    for (const r of redirecciones) expect(ALIAS_DE_RUTAS[r.source]).toBe(r.destination);
  });

  it("la guia se sirve desde su pagina estatica", async () => {
    const reescrituras = (await nextConfig.rewrites!()) as { source: string; destination: string }[];
    expect(reescrituras).toContainEqual({ source: "/informacion", destination: "/informacion.html" });
  });
});
