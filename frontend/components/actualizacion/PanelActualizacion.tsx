"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Card, CardHeader } from "@/components/ui/Card";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { ErrorAdmin, aplicarCarga, obtenerTablerosActualizables, validarCarga, type ArchivoParaEnviar } from "@/lib/api/admin";
import type { CatalogoActualizacion, ResultadoCarga, SesionAdmin, TableroActualizable } from "@/lib/api/types";
import { useAsyncResource } from "@/lib/hooks/useAsyncResource";
import { useEstadoUrl, type EsquemaUrl } from "@/lib/hooks/useEstadoUrl";
import { RUTAS } from "@/lib/rutas";
import { comprimirSiHaceFalta, extensionDe, formatearTamano } from "@/lib/utils/archivos";
import { Bitacora } from "./Bitacora";
import { InformeCarga } from "./InformeCarga";
import { SelectorArchivo } from "./SelectorArchivo";

/** Ruta del tablero que se actualiza, para el enlace «Ver el tablero». */
const RUTA_DEL_TABLERO: Record<string, string> = {
  carbon: RUTAS.carbon, dns: RUTAS.dns, gas: RUTAS.gas, optimizacion: RUTAS.optimizacion, apagon: RUTAS.apagon, apagon_visor: RUTAS.apagon,
};
/** CSV y JSON de más de esto se envían comprimidos (.gz): viajan menos bytes y los grandes caben en el límite de la petición. */
const UMBRAL_COMPRESION = 256 * 1024;

type Fase = "edicion" | "validando" | "validado" | "aplicando" | "aplicada";

export function PanelActualizacion({ sesion, onSalir, onSesionVencida }: { sesion: SesionAdmin; onSalir: () => void; onSesionVencida: () => void }) {
  const catalogo = useAsyncResource((s) => obtenerTablerosActualizables(s), []);
  if (catalogo.error) return <ErrorBloque que="los tableros que puedes actualizar" mensaje={catalogo.error} />;
  if (!catalogo.datos) return <SkeletonChart />;
  return <Actualizador catalogo={catalogo.datos} sesion={sesion} onSalir={onSalir} onSesionVencida={onSesionVencida} />;
}

function Actualizador({ catalogo, sesion, onSalir, onSesionVencida }: { catalogo: CatalogoActualizacion; sesion: SesionAdmin; onSalir: () => void; onSesionVencida: () => void }) {
  const ids = useMemo(() => catalogo.tableros.map((t) => t.id), [catalogo]);
  const esquema = useMemo<EsquemaUrl<{ tablero: string }>>(
    () => ({ tablero: { param: "tablero", defecto: () => "", leer: (c) => ids.find((i) => i === c) } }),
    [ids],
  );
  const [{ tablero: idTablero }, { actualizar }] = useEstadoUrl(esquema);
  const tablero = catalogo.tableros.find((t) => t.id === idTablero) ?? null;

  const [archivos, setArchivos] = useState<Record<string, File | null>>({});
  const [fase, setFase] = useState<Fase>("edicion");
  const [resultado, setResultado] = useState<ResultadoCarga | null>(null);
  const [errores, setErrores] = useState<string[] | undefined>(undefined);
  const [confirmo, setConfirmo] = useState(false);
  const [versionBitacora, setVersionBitacora] = useState(0);

  function reiniciar() {
    setFase("edicion");
    setResultado(null);
    setErrores(undefined);
    setConfirmo(false);
  }

  function elegirTablero(id: string) {
    setArchivos({});
    reiniciar();
    actualizar({ tablero: id });
  }

  function cambiarArchivo(clave: string, archivo: File | null) {
    setArchivos((previos) => ({ ...previos, [clave]: archivo }));
    reiniciar(); // cualquier cambio invalida la revisión anterior: lo que se aplica es lo que se validó
  }

  const seleccionados = tablero ? tablero.archivos.filter((a) => archivos[a.clave]) : [];
  const faltantes = tablero ? tablero.archivos.filter((a) => a.obligatorio && !archivos[a.clave]) : [];
  const formatosMalos = tablero ? seleccionados.filter((a) => !a.formatos.includes(extensionDe(archivos[a.clave]!.name))) : [];
  const listo = tablero !== null && faltantes.length === 0 && formatosMalos.length === 0;

  async function prepararEnvio(t: TableroActualizable): Promise<ArchivoParaEnviar[]> {
    const envio: ArchivoParaEnviar[] = [];
    for (const a of t.archivos) {
      const f = archivos[a.clave];
      if (f) envio.push({ clave: a.clave, archivo: await comprimirSiHaceFalta(f, UMBRAL_COMPRESION) });
    }
    const total = envio.reduce((suma, e) => suma + e.archivo.size, 0);
    if (total > catalogo.limite_total_bytes) {
      throw new ErrorAdmin("Los archivos pesan demasiado para enviarse juntos", 413, [
        `Suman ${formatearTamano(total)} y el máximo por envío es ${formatearTamano(catalogo.limite_total_bytes)}.`,
      ]);
    }
    return envio;
  }

  function manejarError(e: unknown) {
    if (e instanceof ErrorAdmin && e.status === 401) {
      onSesionVencida();
      return;
    }
    setErrores(e instanceof ErrorAdmin && e.errores.length > 0 ? e.errores : [e instanceof Error ? e.message : "Ocurrió un error inesperado"]);
    setFase("edicion");
  }

  async function validar() {
    if (!tablero) return;
    setFase("validando");
    setErrores(undefined);
    try {
      const r = await validarCarga(tablero.id, await prepararEnvio(tablero), sesion.token_csrf);
      setResultado(r);
      setFase(r.valido ? "validado" : "edicion");
    } catch (e) {
      manejarError(e);
    } finally {
      setVersionBitacora((v) => v + 1);
    }
  }

  async function aplicar() {
    if (!tablero || !resultado) return;
    setFase("aplicando");
    setErrores(undefined);
    try {
      const huellas = Object.fromEntries(resultado.huellas.map((h) => [h.clave, h.sha256]));
      const r = await aplicarCarga(tablero.id, await prepararEnvio(tablero), huellas, sesion.token_csrf);
      setResultado(r);
      setFase("aplicada");
    } catch (e) {
      setResultado(null);
      manejarError(e);
    } finally {
      setVersionBitacora((v) => v + 1);
    }
  }

  const ocupado = fase === "validando" || fase === "aplicando";

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-background-elevated px-5 py-3">
        <p className="text-sm">
          Sesión de <b>{sesion.usuario.nombre}</b> · {sesion.usuario.rol}
        </p>
        <button type="button" onClick={onSalir} className="inline-flex h-9 items-center rounded-lg border px-3 text-xs font-semibold" style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}>
          Cerrar sesión
        </button>
      </div>

      {!catalogo.almacenamiento_persistente && (
        <p role="alert" className="rounded-xl px-4 py-3 text-sm font-medium" style={{ color: "var(--color-alerta)", backgroundColor: "var(--color-alerta-bg)" }}>
          Este entorno no tiene almacenamiento persistente (falta configurar la base externa): puedes revisar archivos, pero no aplicar cambios.
        </p>
      )}

      <Card>
        <CardHeader title="1. Elige el tablero" subtitle="Solo aparecen los que tu cuenta puede actualizar" />
        <div className="px-5 pb-5 pt-3">
          {catalogo.tableros.length === 0 ? (
            <p className="text-sm text-foreground-muted">Tu cuenta no tiene tableros asignados. Pide al administrador que te los asigne.</p>
          ) : (
            <fieldset className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <legend className="sr-only">Tablero a actualizar</legend>
              {catalogo.tableros.map((t) => (
                <label
                  key={t.id}
                  className="flex cursor-pointer gap-3 rounded-xl border p-4 text-sm"
                  style={{ borderColor: t.id === idTablero ? "var(--color-marca)" : "var(--border)", backgroundColor: t.id === idTablero ? "var(--color-marca-bg)" : undefined }}
                >
                  <input type="radio" name="tablero" checked={t.id === idTablero} onChange={() => elegirTablero(t.id)} className="mt-1 accent-[var(--color-marca)]" />
                  <span>
                    <span className="block font-semibold">{t.titulo}</span>
                    <span className="mt-0.5 block text-xs text-foreground-muted">{t.descripcion}</span>
                  </span>
                </label>
              ))}
            </fieldset>
          )}
        </div>
      </Card>

      {tablero && (
        <Card>
          <CardHeader title="2. Carga los archivos" subtitle={`Cada archivo se revisa antes de guardarse. Máximo ${formatearTamano(catalogo.limite_bytes)} por archivo; los CSV y JSON grandes se comprimen solos.`} />
          <div className="grid grid-cols-1 gap-3 px-5 pb-5 pt-3 md:grid-cols-2">
            {tablero.archivos.map((a) => (
              <SelectorArchivo
                key={a.clave}
                requerido={a}
                archivo={archivos[a.clave] ?? null}
                onElegir={(f) => cambiarArchivo(a.clave, f)}
                onQuitar={() => cambiarArchivo(a.clave, null)}
                limite={catalogo.limite_bytes}
              />
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3 px-5 pb-5">
            <button
              type="button"
              onClick={validar}
              disabled={!listo || ocupado}
              className="inline-flex h-10 items-center rounded-lg px-4 text-sm font-semibold text-white disabled:opacity-50"
              style={{ backgroundColor: "var(--color-marca)" }}
            >
              {fase === "validando" ? "Revisando…" : "3. Revisar archivos"}
            </button>
            {!listo && faltantes.length > 0 && <span className="text-xs text-foreground-muted">Falta: {faltantes.map((f) => f.etiqueta).join(", ")}</span>}
          </div>
        </Card>
      )}

      {(resultado || errores) && fase !== "aplicada" && <InformeCarga resultado={resultado} errores={errores} />}

      {tablero && (fase === "validado" || fase === "aplicando") && resultado && (
        <Card>
          <CardHeader title="4. Aplica la actualización" subtitle="Reemplaza los datos actuales del tablero por los de estos archivos" />
          <div className="flex flex-col gap-3 px-5 pb-5 pt-3">
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" checked={confirmo} onChange={(e) => setConfirmo(e.target.checked)} className="mt-0.5 accent-[var(--color-marca)]" />
              Entiendo que esto reemplaza los datos actuales de «{tablero.titulo}» y queda registrado a mi nombre.
            </label>
            <div>
              <button
                type="button"
                onClick={aplicar}
                disabled={!confirmo || ocupado || !catalogo.almacenamiento_persistente}
                className="inline-flex h-10 items-center rounded-lg px-4 text-sm font-semibold text-white disabled:opacity-50"
                style={{ backgroundColor: "var(--color-critico)" }}
              >
                {fase === "aplicando" ? "Aplicando…" : "Aplicar actualización"}
              </button>
            </div>
          </div>
        </Card>
      )}

      {tablero && fase === "aplicada" && resultado && (
        <>
          <InformeCarga resultado={resultado} />
          <div className="flex flex-wrap gap-3">
            <Link href={RUTA_DEL_TABLERO[tablero.id] ?? RUTAS.panel} className="inline-flex h-10 items-center rounded-lg px-4 text-sm font-semibold text-white" style={{ backgroundColor: "var(--color-marca)" }}>
              Ver el tablero
            </Link>
            <button type="button" onClick={() => { setArchivos({}); reiniciar(); }} className="inline-flex h-10 items-center rounded-lg border px-4 text-sm font-semibold" style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}>
              Actualizar otro
            </button>
          </div>
        </>
      )}

      {sesion.usuario.rol === "administrador" && <Bitacora version={versionBitacora} />}
    </div>
  );
}
