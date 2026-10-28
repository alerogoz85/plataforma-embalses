"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import { obtenerAuditoria } from "@/lib/api/admin";
import { useAsyncResource } from "@/lib/hooks/useAsyncResource";
import { formatearMomento } from "@/lib/utils/archivos";

const COLOR: Record<string, string> = { ok: "var(--color-optimo)", rechazado: "var(--color-alerta)", error: "var(--color-critico)" };
const ACCION: Record<string, string> = {
  inicio_sesion: "Inicio de sesión", inicio_sesion_fallido: "Inicio de sesión fallido", cuenta_bloqueada: "Cuenta bloqueada", cierre_sesion: "Cierre de sesión",
  validacion: "Validación de archivos", actualizacion: "Actualización", acceso_denegado: "Acceso denegado",
};

/** Bitácora de accesos y cargas (solo administradores): quién, cuándo, qué tablero y con qué resultado. Se recarga con `version`. */
export function Bitacora({ version }: { version: number }) {
  const { datos, error } = useAsyncResource((s) => obtenerAuditoria(50, s), [version]);
  return (
    <Card>
      <CardHeader title="Bitácora" subtitle="Últimos 50 accesos y cargas" />
      <div className="overflow-x-auto px-5 pb-5 pt-3">
        {error && <p role="alert" className="text-sm" style={{ color: "var(--color-critico)" }}>{error}</p>}
        {datos && (
          <table className="w-full min-w-[720px] border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-border text-foreground-muted">
                {["Fecha", "Usuario", "Acción", "Tablero", "Resultado", "Detalle", "Origen"].map((c) => (
                  <th key={c} scope="col" className="px-2 py-2 font-medium">{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {datos.map((r, i) => (
                <tr key={`${r.momento}-${i}`} className="border-b border-border/60 align-top">
                  <td className="whitespace-nowrap px-2 py-2 tabular-nums">{formatearMomento(r.momento)}</td>
                  <td className="px-2 py-2">{r.usuario || "—"}</td>
                  <td className="px-2 py-2">{ACCION[r.accion] ?? r.accion}</td>
                  <td className="px-2 py-2">{r.tablero ?? "—"}</td>
                  <td className="px-2 py-2 font-semibold" style={{ color: COLOR[r.resultado] }}>{r.resultado}</td>
                  <td className="max-w-[28rem] break-words px-2 py-2 text-foreground-muted">{r.detalle}</td>
                  <td className="px-2 py-2 tabular-nums">{r.ip}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}
