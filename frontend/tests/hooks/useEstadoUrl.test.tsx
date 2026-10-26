import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { escribirEstado, leerEstado, useEstadoUrl, type EsquemaUrl } from "@/lib/hooks/useEstadoUrl";
import { enLista } from "@/lib/utils/url";
import { fijarUrl, urlActual } from "../mocks/navigation";

interface Filtros {
  periodo: 12 | 36 | 60;
  region: string | null;
  orden: "asc" | "desc";
}

const ESQUEMA: EsquemaUrl<Filtros> = {
  periodo: { param: "periodo", defecto: () => 36, leer: enLista([12, 36, 60] as const) },
  region: { param: "region", defecto: () => null, leer: (c) => (c.length <= 10 ? c : undefined) },
  orden: { param: "orden", defecto: () => "asc", leer: enLista(["asc", "desc"] as const) },
};

describe("leerEstado / escribirEstado (puras)", () => {
  it("lee los valores validos y usa el defecto para los ausentes o invalidos", () => {
    expect(leerEstado(ESQUEMA, new URLSearchParams("periodo=12&region=Caribe"))).toEqual({ periodo: 12, region: "Caribe", orden: "asc" });
    expect(leerEstado(ESQUEMA, new URLSearchParams("periodo=7&region=" + "x".repeat(20) + "&orden=raro"))).toEqual({ periodo: 36, region: null, orden: "asc" });
    expect(leerEstado(ESQUEMA, new URLSearchParams())).toEqual({ periodo: 36, region: null, orden: "asc" });
  });

  it("escribe solo lo que difiere del defecto y conserva los parametros ajenos", () => {
    const base = new URLSearchParams("otro=1&periodo=12");
    const q = escribirEstado(ESQUEMA, { periodo: 36, region: "Caribe", orden: "desc" }, base);
    expect(q.toString()).toBe("otro=1&region=Caribe&orden=desc");
  });

  it("un valor nulo o vacio quita el parametro", () => {
    expect(escribirEstado(ESQUEMA, { periodo: 36, region: null, orden: "asc" }, new URLSearchParams("region=Caribe")).toString()).toBe("");
  });
});

describe("useEstadoUrl", () => {
  it("lee el estado de la URL actual", () => {
    fijarUrl("/dns?periodo=60&orden=desc");
    const { result } = renderHook(() => useEstadoUrl(ESQUEMA));
    expect(result.current[0]).toEqual({ periodo: 60, region: null, orden: "desc" });
  });

  it("una URL con basura da el estado por defecto, sin error", () => {
    fijarUrl("/dns?periodo=<script>&region=" + "y".repeat(50) + "&orden=1;2");
    const { result } = renderHook(() => useEstadoUrl(ESQUEMA));
    expect(result.current[0]).toEqual({ periodo: 36, region: null, orden: "asc" });
  });

  it("actualizar cambia la URL (solo lo no-defecto) y el estado se vuelve a leer", () => {
    fijarUrl("/dns");
    const { result } = renderHook(() => useEstadoUrl(ESQUEMA));
    act(() => result.current[1].actualizar({ periodo: 12, region: "Caribe" }));
    expect(urlActual()).toBe("/dns?periodo=12&region=Caribe");
    expect(result.current[0]).toMatchObject({ periodo: 12, region: "Caribe" });
    act(() => result.current[1].actualizar({ periodo: 36 }));
    expect(urlActual()).toBe("/dns?region=Caribe");
  });

  it("dos cambios seguidos en el mismo evento se componen (no se pisan)", () => {
    fijarUrl("/dns");
    const { result } = renderHook(() => useEstadoUrl(ESQUEMA));
    act(() => {
      result.current[1].actualizar({ region: "Caribe" });
      result.current[1].actualizar({ orden: "desc" });
    });
    expect(urlActual()).toBe("/dns?region=Caribe&orden=desc");
  });

  it("restablecer vuelve este esquema al defecto y respeta los parametros de otros", () => {
    fijarUrl("/dns?periodo=12&region=Caribe&q=guavio");
    const { result } = renderHook(() => useEstadoUrl(ESQUEMA));
    act(() => result.current[1].restablecer());
    expect(urlActual()).toBe("/dns?q=guavio");
    expect(result.current[0]).toEqual({ periodo: 36, region: null, orden: "asc" });
  });

  it("no apila entradas en el historial: usa replaceState", () => {
    fijarUrl("/dns");
    const antes = window.history.length;
    const { result } = renderHook(() => useEstadoUrl(ESQUEMA));
    act(() => result.current[1].actualizar({ periodo: 12 }));
    act(() => result.current[1].actualizar({ periodo: 60 }));
    expect(window.history.length).toBe(antes);
  });

  it("dos esquemas con parametros distintos en la misma pagina conviven", () => {
    fijarUrl("/embalses?h=90");
    const otro: EsquemaUrl<{ horizonte: 30 | 90 }> = { horizonte: { param: "h", defecto: () => 30, leer: enLista([30, 90] as const) } };
    const { result } = renderHook(() => ({ a: useEstadoUrl(ESQUEMA), b: useEstadoUrl(otro) }));
    expect(result.current.b[0].horizonte).toBe(90);
    act(() => result.current.a[1].actualizar({ region: "Centro" }));
    expect(urlActual()).toBe("/embalses?h=90&region=Centro");
  });
});
