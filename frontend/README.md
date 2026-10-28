# Frontend — Tableros Analíticos

Sitio Next.js (App Router, React 19, Tailwind, Recharts) con el panel de tableros y los tableros de embalses, carbón térmico,
demanda no atendida, gas, optimización hidrotérmica y riesgo de apagón. La documentación completa del proyecto está en el
[README de la raíz](../README.md).

## Estructura

| Carpeta | Qué hay |
|---|---|
| `app/` | Una carpeta por ruta (`/`, `/embalses`, `/carbon`, `/dns`, `/gas`, `/optimizacion`, `/apagon`, `/actualizar`), `not-found.tsx` (404) y `globals.css` (tokens de la identidad visual) |
| `components/` | `panel/`, `layout/`, `ui/` (compartidos) y un grupo por tablero: `dashboard/` (embalses), `carbon/`, `dns/`, `modelos/` (gas y optimización), `apagon/` (visor interactivo), `actualizacion/` (módulo de carga de archivos con sesión) |
| `lib/rutas.ts` | **Manejador central de rutas**: única fuente de las direcciones, anclas de la guía y alias (también lo usa `next.config.ts`) |
| `lib/tableros.ts` | Registro de tableros: de aquí sale el panel |
| `lib/hooks/useEstadoUrl.ts` | Guarda filtros y alternancias en la URL; los lectores validados están en `lib/utils/url.ts` |
| `lib/api/`, `lib/hooks/`, `lib/utils/` | Cliente y tipos de la API, hooks de datos y utilidades puras |
| `e2e/`, `tests/` | Pruebas de extremo a extremo (Playwright) y unitarias (Vitest) |
| `scripts/capturas-guia.mjs` | Regenera las capturas de la guía `/informacion` |

Para agregar un tablero: carpeta en `app/<ruta>/`, su ruta en `lib/rutas.ts` y una entrada en `lib/tableros.ts`.

## Desarrollo

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URL apunta al backend local (puerto 8000)
npm run dev                  # http://localhost:3000
```

| Comando | Qué hace |
|---|---|
| `npm test` | Pruebas unitarias (Vitest + Testing Library) |
| `npm run test:e2e` | Pruebas de extremo a extremo (Playwright; requiere `npm run build` antes y Chrome instalado) |
| `npm run lint` | ESLint |
| `npm run build` | Build de producción (también verifica los tipos) |
| `node scripts/capturas-guia.mjs` | Regenera las capturas de la guía (API local en el puerto 8000 y `npm run build` hecho) |

## Despliegue

Se despliega solo, por Git, en Vercel (proyecto `tableros-analiticos`, directorio
raíz `frontend/`): cada merge a `main` publica producción en https://tableros-analiticos.vercel.app y cada pull request
genera una vista previa. En Vercel el sitio llama a `/api/v1/*` en su propio dominio y
`next.config.ts` lo reenvía a la API (`API_URL`).
