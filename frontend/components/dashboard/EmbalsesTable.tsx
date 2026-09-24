"use client";

import { useMemo, useState } from "react";

import type { EmbalseResumen } from "@/lib/api/types";
import { urlReporte } from "@/lib/api/client";
import {
  formatearNumeroOpcional,
  formatearPorcentaje,
  formatearPorcentajeOpcional,
  SIN_DATO,
} from "@/lib/utils/formatters";
import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonTableRow } from "@/components/ui/Skeleton";
import { InfoButton } from "@/components/ui/InfoButton";
import { AYUDAS } from "./ayudas";
import { RiskBadge } from "@/components/dashboard/RiskBadge";

type ColumnaOrdenable =
  | "nombre"
  | "region"
  | "pct_volumen_util"
  | "aportes_pct_media"
  | "vertimientos_m3s"
  | "turbinado_m3s"
  | "energia_util_gwh"
  | "dias_autonomia";

const COLUMNAS: { clave: ColumnaOrdenable; etiqueta: string; numerica?: boolean; ayuda?: { titulo: string; contenido: React.ReactNode } }[] = [
  { clave: "nombre", etiqueta: "Embalse", ayuda: AYUDAS.colEmbalse },
  { clave: "region", etiqueta: "Región", ayuda: AYUDAS.colRegion },
  { clave: "pct_volumen_util", etiqueta: "% Vol. útil", numerica: true, ayuda: AYUDAS.colPctVolumen },
  { clave: "aportes_pct_media", etiqueta: "Aportes (% media)", numerica: true, ayuda: AYUDAS.colAportes },
  { clave: "vertimientos_m3s", etiqueta: "Vertimientos m³/s", numerica: true, ayuda: AYUDAS.colVertimientos },
  { clave: "turbinado_m3s", etiqueta: "Turbinado m³/s", numerica: true, ayuda: AYUDAS.colTurbinado },
  { clave: "energia_util_gwh", etiqueta: "Energía útil GWh", numerica: true, ayuda: AYUDAS.colEnergiaUtil },
  { clave: "dias_autonomia", etiqueta: "Autonomía (días)", numerica: true, ayuda: AYUDAS.colAutonomia },
];

export function EmbalsesTable({
  embalses,
  cargando,
  onSeleccionar,
  embalseSeleccionado,
}: {
  embalses: EmbalseResumen[];
  cargando: boolean;
  onSeleccionar: (embalseId: string) => void;
  embalseSeleccionado: string | null;
}) {
  const [busqueda, setBusqueda] = useState("");
  const [orden, setOrden] = useState<{ clave: ColumnaOrdenable; direccion: 1 | -1 }>({
    clave: "pct_volumen_util",
    direccion: 1,
  });

  const filas = useMemo(() => {
    const filtradas = embalses.filter((e) =>
      `${e.nombre} ${e.region}`.toLowerCase().includes(busqueda.toLowerCase()),
    );
    return [...filtradas].sort((a, b) => {
      const va = a[orden.clave] ?? -Infinity;
      const vb = b[orden.clave] ?? -Infinity;
      if (typeof va === "string" && typeof vb === "string") {
        return va.localeCompare(vb) * orden.direccion;
      }
      return ((va as number) - (vb as number)) * orden.direccion;
    });
  }, [embalses, busqueda, orden]);

  function alternarOrden(clave: ColumnaOrdenable) {
    setOrden((previo) =>
      previo.clave === clave
        ? { clave, direccion: previo.direccion === 1 ? -1 : 1 }
        : { clave, direccion: 1 },
    );
  }

  return (
    <Card>
      <CardHeader
        ayuda={AYUDAS.tablaEmbalses}
        title="Embalses"
        subtitle={`${filas.length} de ${embalses.length} registros`}
        action={
          <input
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar embalse o región…"
            className="rounded-lg border border-border-strong bg-background px-3 py-1.5 text-xs text-foreground outline-none focus:ring-2"
            style={{ colorScheme: "inherit" }}
          />
        }
      />
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[820px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-foreground-muted">
              {COLUMNAS.map((columna) => (
                <th
                  key={columna.clave}
                  className="cursor-pointer select-none px-4 py-2.5 font-medium hover:text-foreground"
                  onClick={() => alternarOrden(columna.clave)}
                >
                  <span className="inline-flex items-center gap-1">
                    {columna.etiqueta}
                    {orden.clave === columna.clave && (orden.direccion === 1 ? "↑" : "↓")}
                    {columna.ayuda && (
                      <InfoButton titulo={columna.ayuda.titulo}>{columna.ayuda.contenido}</InfoButton>
                    )}
                  </span>
                </th>
              ))}
              <th className="px-4 py-2.5 font-medium">
                <span className="inline-flex items-center gap-1">
                  Reporte
                  <InfoButton titulo={AYUDAS.colReporte.titulo}>{AYUDAS.colReporte.contenido}</InfoButton>
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {cargando && filas.length === 0 &&
              Array.from({ length: 6 }).map((_, i) => <SkeletonTableRow key={i} />)}

            {!cargando && filas.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-foreground-muted">
                  No hay embalses que coincidan con los filtros aplicados.
                </td>
              </tr>
            )}

            {filas.map((embalse) => (
              <tr
                key={embalse.id}
                onClick={() => onSeleccionar(embalse.id)}
                className={`cursor-pointer border-b border-border/60 transition-colors hover:bg-border/30 ${
                  embalseSeleccionado === embalse.id ? "bg-marca-bg/60" : ""
                }`}
                style={
                  embalseSeleccionado === embalse.id
                    ? { backgroundColor: "var(--color-marca-bg)" }
                    : undefined
                }
              >
                <td className="px-4 py-2.5 font-medium text-foreground">
                  {embalse.nombre}
                  {embalse.es_agregado && (
                    <span className="ml-2 rounded-full border border-border-strong px-1.5 py-0.5 text-[10px] font-normal text-foreground-muted">
                      Agregado
                    </span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-foreground-muted">{embalse.region}</td>
                <td className="px-4 py-2.5 tabular-nums">
                  <div className="flex items-center gap-2">
                    <span className="tabular-nums">{formatearPorcentaje(embalse.pct_volumen_util)}</span>
                    <RiskBadge nivel={embalse.nivel_riesgo} tamano="sm" />
                  </div>
                </td>
                <td className="px-4 py-2.5 tabular-nums text-foreground-muted">
                  {formatearPorcentajeOpcional(embalse.aportes_pct_media)}
                </td>
                <td className="px-4 py-2.5 tabular-nums text-foreground-muted">
                  {formatearNumeroOpcional(embalse.vertimientos_m3s)}
                </td>
                <td className="px-4 py-2.5 tabular-nums text-foreground-muted">
                  {formatearNumeroOpcional(embalse.turbinado_m3s)}
                </td>
                <td className="px-4 py-2.5 tabular-nums text-foreground-muted">
                  {formatearNumeroOpcional(embalse.energia_util_gwh, 0)}
                </td>
                <td className="px-4 py-2.5 tabular-nums text-foreground-muted">
                  {embalse.dias_autonomia ?? SIN_DATO}
                </td>
                <td className="px-4 py-2.5" onClick={(e) => e.stopPropagation()}>
                  <div className="flex gap-2 text-xs font-medium">
                    <a
                      href={urlReporte(embalse.id, "csv")}
                      className="text-marca hover:underline"
                      style={{ color: "var(--color-marca)" }}
                    >
                      CSV
                    </a>
                    <a
                      href={urlReporte(embalse.id, "json")}
                      className="text-marca hover:underline"
                      style={{ color: "var(--color-marca)" }}
                    >
                      JSON
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
