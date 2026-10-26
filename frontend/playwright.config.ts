import { defineConfig } from "@playwright/test";

/**
 * Pruebas de extremo a extremo: abren el sitio de produccion (`next build` + `next start`) en un
 * navegador real, para comprobar lo que las pruebas con jsdom no pueden: que los graficos SVG se
 * dibujan, que el diseno se adapta al celular y que la navegacion funciona.
 *
 * La API se simula en el propio navegador (ver e2e/api.ts): las pruebas no dependen del backend ni
 * de la red. Localmente usan el Chrome instalado (E2E_CHANNEL=chrome, valor por defecto); en CI,
 * el Chromium que instala Playwright (E2E_CHANNEL vacio).
 */
const PUERTO = 3200;

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://localhost:${PUERTO}`,
    channel: process.env.E2E_CHANNEL === undefined ? "chrome" : process.env.E2E_CHANNEL || undefined,
    trace: "retain-on-failure",
  },
  webServer: {
    command: `npx next start -p ${PUERTO}`,
    url: `http://localhost:${PUERTO}`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
