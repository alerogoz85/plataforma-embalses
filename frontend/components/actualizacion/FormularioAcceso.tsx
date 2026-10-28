"use client";

import { useState, type FormEvent } from "react";

import { Card } from "@/components/ui/Card";
import { iniciarSesion } from "@/lib/api/admin";
import type { SesionAdmin } from "@/lib/api/types";

/**
 * Inicio de sesión del módulo de actualización. El mensaje de error es el que entrega la API (siempre el mismo para usuario o
 * contraseña incorrectos: no revela qué cuentas existen). La contraseña nunca se guarda en la página ni en el almacenamiento del navegador.
 */
export function FormularioAcceso({ onSesion }: { onSesion: (s: SesionAdmin) => void }) {
  const [usuario, setUsuario] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      const sesion = await iniciarSesion(usuario, contrasena);
      setContrasena("");
      onSesion(sesion);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible iniciar sesión");
      setContrasena("");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Card className="mx-auto w-full max-w-md">
      <form onSubmit={enviar} className="flex flex-col gap-4 p-6" aria-label="Iniciar sesión">
        <div>
          <h2 className="text-lg font-bold" style={{ color: "var(--color-marca-oscuro)" }}>
            Acceso para actualizar los tableros
          </h2>
          <p className="mt-1 text-sm text-foreground-muted">Solo para personas autorizadas. Cada acceso y cada carga queda registrado.</p>
        </div>
        <label className="flex flex-col gap-1.5 text-sm font-medium">
          Usuario
          <input
            className="campo-select"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            maxLength={80}
            required
          />
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium">
          Contraseña
          <input
            className="campo-select"
            type="password"
            value={contrasena}
            onChange={(e) => setContrasena(e.target.value)}
            autoComplete="current-password"
            maxLength={200}
            required
          />
        </label>
        {error && (
          <p role="alert" className="rounded-lg px-3 py-2 text-sm font-medium" style={{ color: "var(--color-critico)", backgroundColor: "var(--color-critico-bg)" }}>
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={enviando || !usuario || !contrasena}
          className="inline-flex h-10 items-center justify-center rounded-lg px-4 text-sm font-semibold text-white transition-opacity disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
          style={{ backgroundColor: "var(--color-marca)" }}
        >
          {enviando ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </Card>
  );
}
