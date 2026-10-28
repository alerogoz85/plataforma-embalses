"use client";

import { useEffect, useState } from "react";

import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { ErrorAdmin, cerrarSesion, obtenerSesion } from "@/lib/api/admin";
import type { SesionAdmin } from "@/lib/api/types";
import { FormularioAcceso } from "./FormularioAcceso";
import { PanelActualizacion } from "./PanelActualizacion";

type Estado = { tipo: "cargando" } | { tipo: "sin_sesion"; aviso?: string } | { tipo: "error"; mensaje: string } | { tipo: "con_sesion"; sesion: SesionAdmin };

/**
 * Módulo de actualización de tableros. Es la única parte del sitio que escribe: exige iniciar sesión, y el servidor vuelve a comprobar
 * permisos y archivos en cada paso (esta pantalla es comodidad, no la barrera de seguridad).
 */
export function ModuloActualizacion() {
  const [estado, setEstado] = useState<Estado>({ tipo: "cargando" });

  useEffect(() => {
    const controlador = new AbortController();
    obtenerSesion(controlador.signal)
      .then((sesion) => setEstado({ tipo: "con_sesion", sesion }))
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (e instanceof ErrorAdmin && e.status === 401) setEstado({ tipo: "sin_sesion" });
        else setEstado({ tipo: "error", mensaje: e instanceof Error ? e.message : "No fue posible consultar la sesión" });
      });
    return () => controlador.abort();
  }, []);

  async function salir() {
    if (estado.tipo !== "con_sesion") return;
    try {
      await cerrarSesion(estado.sesion.token_csrf);
    } finally {
      setEstado({ tipo: "sin_sesion" });
    }
  }

  return (
    <div className="flex min-h-full flex-col">
      <Header titulo="Actualizar los tableros" subtitulo="Carga de archivos con acceso protegido" />
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-5 px-4 py-8 sm:px-6">
        <div>
          <h1 className="text-2xl font-extrabold" style={{ color: "var(--color-marca-oscuro)" }}>
            Actualización de tableros
          </h1>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-foreground-muted">
            Sube los archivos nuevos de un modelo (Excel, CSV, JSON o Parquet). Se revisan antes de guardarse: si algo no cumple, no se cambia nada y verás el motivo.
          </p>
        </div>

        {estado.tipo === "cargando" && <SkeletonChart />}
        {estado.tipo === "error" && <p role="alert" className="text-sm" style={{ color: "var(--color-critico)" }}>{estado.mensaje}</p>}
        {estado.tipo === "sin_sesion" && (
          <>
            {estado.aviso && <p role="status" className="rounded-xl px-4 py-3 text-sm" style={{ color: "var(--color-alerta)", backgroundColor: "var(--color-alerta-bg)" }}>{estado.aviso}</p>}
            <FormularioAcceso onSesion={(sesion) => setEstado({ tipo: "con_sesion", sesion })} />
          </>
        )}
        {estado.tipo === "con_sesion" && (
          <PanelActualizacion sesion={estado.sesion} onSalir={salir} onSesionVencida={() => setEstado({ tipo: "sin_sesion", aviso: "La sesión venció. Inicia sesión de nuevo." })} />
        )}
      </main>
      <Footer>Solo personal autorizado del Ministerio de Minas y Energía. Cada acceso y cada carga queda registrado.</Footer>
    </div>
  );
}
