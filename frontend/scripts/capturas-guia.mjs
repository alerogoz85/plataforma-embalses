// Regenera las capturas de la guia (public/informacion/img/*.jpg) con los datos reales de la API local.
// Uso (API en :8000 con la base al dia, y `npm run build` hecho):
//   node scripts/capturas-guia.mjs                 -> tablero de embalses (16 capturas)
//   node scripts/capturas-guia.mjs panel carbon dns apagon   -> las paginas completas indicadas (y sus zonas medidas)
import { execFileSync, spawn } from "node:child_process";
import { mkdirSync, rmSync } from "node:fs";
import { chromium } from "@playwright/test";

const PUERTO = 3300;
const SALIDA = new URL("../public/informacion/img/", import.meta.url).pathname;
const TMP = "/tmp/capturas-guia";
mkdirSync(TMP, { recursive: true });

// detached + grupo de procesos: `npx` lanza a `next` como hijo y matar solo a `npx` lo dejaba vivo en el puerto.
const servidor = spawn("npx", ["next", "start", "-p", String(PUERTO)], { stdio: "ignore", detached: true });
const detenerServidor = () => { try { process.kill(-servidor.pid); } catch {} };
for (let i = 0; i < 60; i++) {
  try { if ((await fetch(`http://localhost:${PUERTO}`)).ok) break; } catch {}
  await new Promise((r) => setTimeout(r, 1000));
}

// --disable-web-security: el sitio de capturas corre en otro puerto que el permitido por CORS de la API.
const navegador = await chromium.launch({ channel: "chrome", args: ["--disable-web-security"] });

async function pagina(ruta, { ancho = 1360, alto = 900, oscuro = false } = {}) {
  const ctx = await navegador.newContext({ viewport: { width: ancho, height: alto }, deviceScaleFactor: 1, colorScheme: oscuro ? "dark" : "light" });
  const p = await ctx.newPage();
  await p.goto(`http://localhost:${PUERTO}${ruta}`);
  await p.waitForLoadState("networkidle");
  await p.waitForTimeout(1500);
  return p;
}

async function guardar(p, nombre, clip, opts = {}) {
  const png = `${TMP}/${nombre}.png`;
  await p.screenshot({ path: png, fullPage: true, ...(clip ? { clip: { x: clip[0], y: clip[1], width: clip[2], height: clip[3] } } : {}), ...opts });
  execFileSync("sips", ["-s", "format", "jpeg", "-s", "formatOptions", "82", png, "--out", `${SALIDA}${nombre}.jpg`], { stdio: "ignore" });
  console.log("ok", nombre);
}

const PAGINAS = { panel: "/", carbon: "/carbon", dns: "/dns", apagon: "/apagon" };
const pedidas = process.argv.slice(2);

try {
  if (pedidas.length > 0) {
    for (const nombre of pedidas) {
      const ruta = PAGINAS[nombre];
      if (!ruta) throw new Error(`Pagina desconocida: ${nombre} (opciones: ${Object.keys(PAGINAS).join(", ")})`);
      const p = await pagina(ruta);
      await p.waitForTimeout(2000);
      // Zonas (x, y, ancho, alto) de los bloques de primer nivel: sirven para los marcadores de la guia.
      const zonas = await p.evaluate(() => {
        const r = (e) => { const b = e.getBoundingClientRect(); return [Math.round(b.x + scrollX), Math.round(b.y + scrollY), Math.round(b.width), Math.round(b.height)]; };
        const m = document.querySelector("main");
        return { articulos: [...document.querySelectorAll("article")].map(r), alto: document.documentElement.scrollHeight, header: r(document.querySelector("header")), footer: r(document.querySelector("footer")),
                 bloques: [...m.children].map((e) => [...e.children].length > 1 && e.className.includes("grid") ? [...e.children].map(r) : r(e)) };
      });
      console.log(nombre, JSON.stringify(zonas));
      await guardar(p, nombre, null);
      await p.context().close();
    }
    detenerServidor();
    process.exit(0);
  }

  // Estado por defecto: total nacional, 1 mes en el principal y 12 en la senda.
  let p = await pagina("/embalses");
  const alto = await p.evaluate(() => document.documentElement.scrollHeight);
  console.log("alto de pagina", alto);
  await guardar(p, "general", null);
  await guardar(p, "header", [0, 0, 1360, 123]);
  await guardar(p, "filtros", [56, 135, 1248, 173]);
  await guardar(p, "filtros-todos", [56, 135, 1248, 173]);
  await guardar(p, "kpis", [56, 312, 1248, 148]);
  await guardar(p, "main12", [56, 464, 832, 412]);
  await guardar(p, "region", [888, 464, 416, 412]);
  await guardar(p, "senda", [56, 880, 1248, 586]);
  await guardar(p, "tabla", [56, 1470, 1248, 656]);

  // Ayuda al pasar el cursor por el ⓘ de la primera tarjeta.
  await p.getByRole("button", { name: /Ayuda: % Volumen útil/ }).first().hover();
  await p.waitForTimeout(400);
  await guardar(p, "ayuda-hover", [54, 305, 520, 330], { fullPage: false });
  await p.mouse.move(700, 5);

  // Principal a 12 meses.
  await p.getByRole("button", { name: "12m" }).first().click();
  await p.waitForTimeout(1500);
  await guardar(p, "main-total-12m", [56, 464, 832, 412]);

  // Senda a 3 meses (segundo grupo de botones «3m» de la pagina).
  await p.getByRole("button", { name: "3m" }).last().click();
  await p.waitForTimeout(1500);
  await guardar(p, "senda-3m", [56, 880, 1248, 586]);
  await p.context().close();

  // Agregado Bogota: senda con respaldo Holt-Winters y su tabla de validacion.
  p = await pagina("/embalses");
  await p.getByRole("combobox", { name: "Embalse" }).selectOption({ label: "Agregado Bogotá" });
  await p.waitForTimeout(2500);
  await guardar(p, "senda-bogota", [56, 880, 1248, 716]);
  await p.context().close();

  // Region Centro con todos los embalses.
  p = await pagina("/embalses");
  await p.getByRole("combobox", { name: "Región" }).selectOption("Centro");
  await p.waitForTimeout(2500);
  await guardar(p, "region-centro", [0, 135, 1360, 709]);
  await p.context().close();

  // Tema oscuro y celular.
  p = await pagina("/embalses", { oscuro: true });
  await p.evaluate(() => document.documentElement.classList.add("dark"));
  await p.waitForTimeout(500);
  await guardar(p, "oscuro", [0, 0, 1360, 1100]);
  await p.context().close();

  p = await pagina("/embalses", { ancho: 400, alto: 900 });
  await guardar(p, "movil", [0, 0, 400, 1500]);
  await p.context().close();
} finally {
  await navegador.close().catch(() => {});
  detenerServidor();
  rmSync(TMP, { recursive: true, force: true });
}
