import { expect, test } from "@playwright/test";

import { conResultados } from "../tests/modelos/fixturesModelos";
import { simularApi } from "./api";

test.describe("Panel de tableros", () => {
  test("muestra los dos tableros y navega a cada uno", async ({ page }) => {
    await simularApi(page);
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1, name: "Plataforma de Tableros Analíticos" })).toBeVisible();

    await page.getByRole("link", { name: "Abrir el tablero de Carbón térmico" }).click();
    await expect(page).toHaveURL(/\/carbon$/);
    await expect(page.getByRole("heading", { level: 1, name: "Modelo de carbón térmico" })).toBeVisible();

    await page.getByRole("link", { name: "Tableros" }).click();
    await expect(page).toHaveURL(/\/$/);
    await page.getByRole("link", { name: "Abrir el tablero de Embalses" }).click();
    await expect(page).toHaveURL(/\/embalses$/);
  });

  test("el titulo de la pestana cambia por tablero", async ({ page }) => {
    await simularApi(page);
    await page.goto("/carbon");
    await expect(page).toHaveTitle("Modelo de carbón térmico · Tableros Analíticos");
    await page.goto("/embalses");
    await expect(page).toHaveTitle("Monitoreo de Embalses · Tableros Analíticos");
  });

  test("la guia /informacion se sirve y trae los capitulos de carbon", async ({ page }) => {
    await page.goto("/informacion");
    await expect(page.locator("#carbon-mapa")).toBeAttached();
    await expect(page.locator("#panel .hs")).toHaveCount(4); // marcadores interactivos del panel
  });
});

test.describe("Tablero DNS con el navegador real", () => {
  test("se abre desde el panel y dibuja sus graficos", async ({ page }) => {
    await simularApi(page);
    await page.goto("/");
    await page.getByRole("link", { name: "Abrir el tablero de Demanda no atendida" }).click();
    await expect(page).toHaveURL(/\/dns$/);
    await expect(page.getByRole("heading", { level: 1, name: "Demanda no atendida (DNS)" })).toBeVisible();
    await expect(page).toHaveTitle("Demanda no atendida (DNS) · Tableros Analíticos");
    await expect(page.locator(".recharts-bar-rectangle").first()).toBeVisible();
    expect(await page.locator(".recharts-wrapper").count()).toBeGreaterThanOrEqual(4); // serie + 3 patrones
  });

  test("elegir una region consulta todos los bloques con ella y la subarea queda limitada", async ({ page }) => {
    const llamadas = await simularApi(page);
    await page.goto("/dns");
    await expect(page.getByText("5.963")).toBeVisible();
    await page.getByRole("combobox", { name: "Región" }).selectOption("Norte");
    await expect.poll(() => llamadas.filter((u) => u.searchParams.get("region") === "Norte").map((u) => u.pathname.split("/").pop()).sort())
      .toEqual(["causas", "cambios-reporte", "modelo", "patrones", "resumen", "serie", "zonas"].sort());
    await expect(page.getByRole("combobox", { name: "Subárea" }).locator("option")).toHaveCount(3);
  });

  test("en celular /dns no tiene desplazamiento horizontal", async ({ page }) => {
    await simularApi(page);
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/dns");
    await page.waitForLoadState("networkidle");
    const { ancho, visible } = await page.evaluate(() => ({ ancho: document.documentElement.scrollWidth, visible: window.innerWidth }));
    expect(ancho).toBeLessThanOrEqual(visible);
  });
});

test.describe("Tableros de modelos analiticos (gas, optimizacion, apagon)", () => {
  for (const [ruta, titulo] of [["/gas", "Gas natural: oferta declarada y fiscalizada"], ["/optimizacion", "Optimización hidrotérmica (SDDP)"], ["/apagon", "Riesgo de apagón condicionado por ENOS"]]) {
    test(`${ruta} sin resultados muestra la ficha y como cargarlos, sin graficos`, async ({ page }) => {
      await simularApi(page);
      await page.goto(ruta);
      await expect(page.getByRole("heading", { level: 1, name: titulo })).toBeVisible();
      await expect(page.getByText("Aún no hay resultados cargados")).toBeVisible();
      await expect(page.getByText("Ficha del modelo")).toBeVisible();
      await expect(page.locator(".recharts-wrapper")).toHaveCount(0);
    });
  }

  test("el panel muestra los seis tableros", async ({ page }) => {
    await simularApi(page);
    await page.goto("/");
    await expect(page.getByRole("region", { name: "Tableros disponibles" }).getByRole("link")).toHaveCount(6);
  });

  test("con resultados importados dibuja los graficos y el filtro de periodo los recorta a todos", async ({ page }) => {
    await simularApi(page, { apagon: conResultados() });
    await page.goto("/apagon");
    await expect(page.locator(".recharts-line-curve")).toHaveCount(2);
    // El déficit de octubre vale 0: una barra de altura cero no se dibuja, así que hay 2 de las 3.
    await expect(page.locator(".recharts-bar-rectangle")).toHaveCount(2);
    await page.getByRole("combobox", { name: "Desde" }).selectOption("2026-12");
    await expect(page.locator(".recharts-bar-rectangle")).toHaveCount(1);
    await expect(page.locator(".recharts-yAxis-tick-labels").first()).toBeVisible();
    await page.getByRole("button", { name: /Restablecer filtros/ }).click();
    await expect(page.locator(".recharts-bar-rectangle")).toHaveCount(2);
  });

  for (const ruta of ["/gas", "/optimizacion", "/apagon"]) {
    test(`en celular ${ruta} no tiene desplazamiento horizontal (con resultados)`, async ({ page }) => {
      await simularApi(page, { gas: conResultados(undefined, "gas"), optimizacion: conResultados(undefined, "optimizacion"), apagon: conResultados() });
      await page.setViewportSize({ width: 375, height: 812 });
      await page.goto(ruta);
      await page.waitForLoadState("networkidle");
      const { ancho, visible } = await page.evaluate(() => ({ ancho: document.documentElement.scrollWidth, visible: window.innerWidth }));
      expect(ancho).toBeLessThanOrEqual(visible);
    });
  }
});

test.describe("Graficos realmente dibujados (lo que jsdom no ve)", () => {
  test("carbon: linea, banda, techo y record, barras e inventario se pintan como SVG", async ({ page }) => {
    await simularApi(page);
    await page.goto("/carbon");
    await expect(page.locator(".recharts-line-curve")).toHaveCount(4); // observado + P50 del principal; P50 + XM de la comparacion
    await expect(page.locator(".recharts-area-area").first()).toBeVisible();
    await expect(page.locator(".recharts-reference-line")).toHaveCount(3); // techo y record + techo en XM
    await expect(page.locator(".recharts-bar-rectangle")).toHaveCount(3 + 2 * 2); // 3 trimestres + 2 meses x (P50, P90)
    // Cada curva tiene trazo real (no un path vacio).
    for (const d of await page.locator(".recharts-line-curve").evaluateAll((els) => els.map((e) => e.getAttribute("d")))) {
      expect(d && d.length > 10).toBeTruthy();
    }
  });

  test("embalses: el grafico principal, la regional y la senda se pintan", async ({ page }) => {
    await simularApi(page);
    await page.goto("/embalses");
    await expect(page.locator(".recharts-line-curve").first()).toBeVisible();
    await expect(page.locator(".recharts-bar-rectangle").first()).toBeVisible();
    expect(await page.locator(".recharts-wrapper").count()).toBeGreaterThanOrEqual(3);
  });
});

test.describe("Filtros del tablero de carbon, con el navegador real", () => {
  test("cambiar la unidad reescala el eje sin volver a consultar", async ({ page }) => {
    const llamadas = await simularApi(page);
    await page.goto("/carbon");
    // Etiquetas del eje Y del grafico principal (el primero de la pagina): en GBTU/dia el eje cubre el techo (400).
    const eje = page.locator(".recharts-yAxis-tick-labels").first();
    await expect(eje).toContainText("420");
    const antes = llamadas.length;
    await page.getByRole("combobox", { name: "Unidad" }).selectOption("kt");
    await expect(eje).not.toContainText("400");
    await expect(page.getByText("Consumo de carbón térmico (kt/día)")).toBeVisible();
    expect(llamadas.length).toBe(antes);
  });

  test("cambiar el horizonte consulta de nuevo los bloques que dependen de el", async ({ page }) => {
    const llamadas = await simularApi(page);
    await page.goto("/carbon");
    await expect(page.locator(".recharts-line-curve")).toHaveCount(4);
    await page.getByRole("combobox", { name: "Horizonte" }).selectOption("3");
    await expect.poll(() => llamadas.filter((u) => u.searchParams.get("horizonte_meses") === "3").map((u) => u.pathname.split("/").pop()).sort())
      .toEqual(["comparacion-xm", "inventario", "resumen", "serie"]);
  });

  test("Restablecer filtros vuelve a los valores por defecto", async ({ page }) => {
    await simularApi(page);
    await page.goto("/carbon");
    await page.getByRole("combobox", { name: "Horizonte" }).selectOption("1");
    await page.getByRole("combobox", { name: "Unidad" }).selectOption("kt");
    await page.getByRole("button", { name: /Restablecer filtros/ }).click();
    await expect(page.getByRole("combobox", { name: "Horizonte" })).toHaveValue("9");
    await expect(page.getByRole("combobox", { name: "Unidad" })).toHaveValue("gbtu");
  });

  test("el boton ⓘ muestra su ayuda al pasar el cursor", async ({ page }) => {
    await simularApi(page);
    await page.goto("/carbon");
    await page.getByRole("button", { name: "Ayuda: Filtro de horizonte" }).hover();
    await expect(page.getByRole("note")).toContainText("Cuántos meses hacia adelante");
  });
});

test.describe("Diseno adaptable y tema", () => {
  for (const ruta of ["/", "/embalses", "/carbon"]) {
    test(`en celular ${ruta} no tiene desplazamiento horizontal`, async ({ page }) => {
      await simularApi(page);
      await page.setViewportSize({ width: 375, height: 812 });
      await page.goto(ruta);
      await page.waitForLoadState("networkidle");
      const { ancho, visible } = await page.evaluate(() => ({ ancho: document.documentElement.scrollWidth, visible: window.innerWidth }));
      expect(ancho).toBeLessThanOrEqual(visible);
    });
  }

  test("el modo oscuro se aplica y se recuerda al recargar", async ({ page }) => {
    await simularApi(page);
    await page.goto("/carbon");
    await page.getByRole("button", { name: /Cambiar a modo oscuro/ }).click();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await page.reload();
    await expect(page.locator("html")).toHaveClass(/dark/);
  });

  test("si la API falla, cada bloque muestra su error sin romper la pagina", async ({ page }) => {
    await page.route("**/api/v1/**", (r) => r.fulfill({ status: 404, json: { detalle: "modelo no cargado" } }));
    await page.goto("/carbon");
    await expect(page.getByText(/No fue posible cargar los indicadores: modelo no cargado/)).toBeVisible();
    await expect(page.getByRole("button", { name: /Restablecer filtros/ })).toBeVisible();
  });
});
