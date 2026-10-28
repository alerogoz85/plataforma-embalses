import type { CatalogoActualizacion, RegistroAuditoria, ResultadoCarga, SesionAdmin } from "@/lib/api/types";

export const crearSesion = (sobre: Partial<SesionAdmin["usuario"]> = {}): SesionAdmin => ({
  usuario: { nombre_usuario: "ana", nombre: "Ana Pérez", rol: "administrador", tableros: ["gas", "optimizacion"], ...sobre },
  token_csrf: "csrf-de-prueba",
  vence_en: "2026-10-28T05:00:00Z",
});

export const crearCatalogoAdmin = (sobre: Partial<CatalogoActualizacion> = {}): CatalogoActualizacion => ({
  tableros: [
    {
      id: "optimizacion", titulo: "Optimización hidrotérmica", descripcion: "Resumen de la corrida SDDP.",
      archivos: [
        { clave: "resumen", etiqueta: "Resumen de la corrida (JSON)", formatos: ["json"], obligatorio: true, descripcion: "", patron_nombre: null },
        { clave: "manifest", etiqueta: "Manifiesto (JSON)", formatos: ["json"], obligatorio: false, descripcion: "", patron_nombre: null },
      ],
    },
    {
      id: "gas", titulo: "Gas natural", descripcion: "Pronóstico por campo.",
      archivos: [{ clave: "v2", etiqueta: "Pronóstico v2 (Excel)", formatos: ["xlsx"], obligatorio: true, descripcion: "Libro con hojas.", patron_nombre: null }],
    },
  ],
  limite_bytes: 4 * 1024 * 1024, limite_total_bytes: 4_400_000, limite_contenido_bytes: 60 * 1024 * 1024, almacenamiento_persistente: true,
  ...sobre,
});

export const crearResultadoCarga = (sobre: Partial<ResultadoCarga> = {}): ResultadoCarga => ({
  tablero: "optimizacion", valido: true, aplicada: false,
  resumen: [{ etiqueta: "Indicadores", valor: "3" }, { etiqueta: "Origen", valor: "Modelo SDDP" }],
  errores: [], advertencias: ["La corrida no es publicable."],
  huellas: [{ clave: "resumen", sha256: "a".repeat(64) }],
  ...sobre,
});

export const crearAuditoria = (): RegistroAuditoria[] => [
  { momento: "2026-10-27T15:00:00Z", usuario: "ana", accion: "actualizacion", tablero: "optimizacion", resultado: "ok", detalle: "1 archivo(s)", ip: "10.0.0.1" },
  { momento: "2026-10-27T14:59:00Z", usuario: "ana", accion: "inicio_sesion", tablero: null, resultado: "ok", detalle: "sesión iniciada", ip: "10.0.0.1" },
];
