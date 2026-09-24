# Frontend — Plataforma de Monitoreo de Embalses

Dashboard Next.js (App Router, React 19, Tailwind, Recharts). La documentación
completa del proyecto está en el [README de la raíz](../README.md).

## Desarrollo

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URL apunta al backend local (puerto 8000)
npm run dev                  # http://localhost:3000
```

| Comando | Qué hace |
|---|---|
| `npm test` | Pruebas (Vitest + Testing Library) |
| `npm run lint` | ESLint |
| `npm run build` | Build de producción (también verifica los tipos) |

## Despliegue

Se despliega solo, por Git, en Vercel (proyecto `plataforma-embalses`, directorio
raíz `frontend/`): cada merge a `main` publica producción y cada pull request genera
una vista previa. En Vercel el sitio llama a `/api/v1/*` en su propio dominio y
`next.config.ts` lo reenvía a la API (`API_URL`).
