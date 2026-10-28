import { expect, test } from "@playwright/test";

import { conResultados, crearResultadoConDimensiones } from "../tests/modelos/fixturesModelos";
import { simularApi } from "./api";

test.describe("DNS: simetria de los paneles largos", () => {
  const alto = async (page: import("@playwright/test").Page, titulo: string) =>
    Math.round((await page.getByRole("heading", { name: titulo, level: 2 }).locator("xpath=ancestor::div[contains(@class,'rounded-2xl')][1]").boundingBox())!.height);

  test("por defecto cada panel mide lo mismo que su vecino; ampliar y volver a contraer restablece la simetria", async ({ page }) => {
    await simularApi(page);
    await page.setViewportSize({ width: 1360, height: 900 });
    await page.goto("/dns");
    await expect(page.getByRole("button", { name: "Ver todo (2 zonas)" })).toBeVisible();
    expect(await alto(page, "Priorización de zonas")).toBe(await alto(page, "Causas de los eventos"));
    expect(await alto(page, "Modelo predictivo")).toBe(await alto(page, "Cambios en la forma de reportar"));

    await page.getByRole("button", { name: /^Ver todo \(2 subáreas/ }).click();
    await expect(page).toHaveURL(/ampliar=modelo$/);
    await expect(page.getByRole("button", { name: "Ver menos" })).toHaveAttribute("aria-expanded", "true");
    await page.getByRole("button", { name: "Ver menos" }).click();
    await expect(page).not.toHaveURL(/ampliar/);
    expect(await alto(page, "Modelo predictivo")).toBe(await alto(page, "Cambios en la forma de reportar"));
  });

  test("ampliado muestra todo el contenido del panel (sin zona desplazable) y la direccion lo conserva al recargar", async ({ page }) => {
    await simularApi(page);
    await page.setViewportSize({ width: 1360, height: 900 });
    await page.goto("/dns?ampliar=zonas,modelo");
    await expect(page.getByRole("button", { name: "Ver menos" })).toHaveCount(2);
    await expect(page.getByRole("region", { name: "Contenido desplazable" })).toHaveCount(0);
    await page.reload();
    await expect(page.getByRole("button", { name: "Ver menos" })).toHaveCount(2);
  });

  test("en pantallas angostas los paneles tienen altura maxima y no desbordan horizontalmente", async ({ page }) => {
    await simularApi(page);
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/dns");
    await expect(page.getByRole("button", { name: "Ver todo (2 zonas)" })).toBeVisible();
    const { ancho, visible } = await page.evaluate(() => ({ ancho: document.documentElement.scrollWidth, visible: window.innerWidth }));
    expect(ancho).toBeLessThanOrEqual(visible);
  });
});

test.describe("Rutas: manejador central, alias y 404", () => {
  test("los alias redirigen a la ruta canonica", async ({ page }) => {
    await simularApi(page);
    for (const [alias, destino] of [["/tableros", "/"], ["/demanda-no-atendida", "/dns"], ["/riesgo-apagon", "/apagon"], ["/embalse", "/embalses"]]) {
      await page.goto(alias);
      await expect(page).toHaveURL(new RegExp(`${destino === "/" ? "/$" : destino + "$"}`));
    }
  });

  test("una direccion que no existe muestra la pagina 404 con el camino de vuelta", async ({ page }) => {
    const respuesta = await page.goto("/no-existe");
    expect(respuesta?.status()).toBe(404);
    await expect(page.getByRole("heading", { name: "No encontramos esa página" })).toBeVisible();
    await page.getByRole("link", { name: "Ir al panel de tableros" }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("la guia de cada tarjeta lleva a su capitulo", async ({ page }) => {
    await simularApi(page);
    await page.goto("/");
    await page.getByRole("link", { name: "Guía del tablero de Demanda no atendida" }).click();
    await expect(page).toHaveURL(/\/informacion#dns-mapa$/);
    await expect(page.locator("#dns-mapa")).toBeVisible();
  });
});

test.describe("Cada vista y cada filtro tienen su direccion (URL)", () => {
  test("DNS: un enlace con filtros abre el tablero filtrado, y recargar conserva la vista", async ({ page }) => {
    const llamadas = await simularApi(page);
    await page.goto("/dns?periodo=12&region=Norte&origen=programada&medida=energia");
    await expect(page.getByRole("combobox", { name: "Período" })).toHaveValue("12");
    await expect(page.getByRole("combobox", { name: "Región" })).toHaveValue("Norte");
    await expect(page.getByRole("combobox", { name: "Origen" })).toHaveValue("programada");
    await expect(page.getByText("Energía no atendida (GWh) por mes")).toBeVisible();
    expect(llamadas.some((u) => u.pathname.endsWith("/dns/resumen") && u.search === "?periodo_meses=12&origen=programada&region=Norte")).toBe(true);
    await page.reload();
    await expect(page.getByRole("combobox", { name: "Período" })).toHaveValue("12");
  });

  test("DNS: cambiar un filtro cambia la URL sin recargar y restablecer la limpia", async ({ page }) => {
    await simularApi(page);
    await page.goto("/dns");
    await expect(page.getByText("5.963")).toBeVisible();
    await page.getByRole("combobox", { name: "Período" }).selectOption("60");
    await expect(page).toHaveURL(/\/dns\?periodo=60$/);
    await page.getByRole("combobox", { name: "Región" }).selectOption("Norte");
    await expect(page).toHaveURL(/periodo=60&region=Norte$/);
    await page.getByRole("button", { name: /Restablecer filtros/ }).click();
    await expect(page).toHaveURL(/\/dns$/);
  });

  test("cambiar filtros no apila entradas en el historial: «atras» vuelve al panel", async ({ page }) => {
    await simularApi(page);
    await page.goto("/");
    await page.getByRole("link", { name: "Abrir el tablero de Carbón térmico" }).click();
    await expect(page).toHaveURL(/\/carbon$/);
    await page.getByRole("combobox", { name: "Horizonte" }).selectOption("3");
    await page.getByRole("combobox", { name: "Unidad" }).selectOption("kt");
    await expect(page).toHaveURL(/horizonte=3&unidad=kt$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/$/);
  });

  test("valores invalidos en la URL se ignoran sin errores", async ({ page }) => {
    await simularApi(page);
    const errores: string[] = [];
    page.on("pageerror", (e) => errores.push(e.message));
    await page.goto("/carbon?horizonte=2&unidad=lb&dias=99&historia=x");
    await expect(page.getByRole("combobox", { name: "Horizonte" })).toHaveValue("9");
    await expect(page.getByRole("combobox", { name: "Unidad" })).toHaveValue("gbtu");
    expect(errores).toEqual([]);
  });

  test("embalses: region, horizonte de la senda y busqueda de la tabla viven en la URL", async ({ page }) => {
    await simularApi(page);
    await page.goto("/embalses?region=Centro&hs=6&q=guav");
    await expect(page.getByRole("combobox", { name: "Región" }).first()).toHaveValue("Centro");
    await expect(page.getByPlaceholder("Buscar embalse o región…")).toHaveValue("guav");
    await page.getByPlaceholder("Buscar embalse o región…").fill("");
    await expect(page).not.toHaveURL(/q=/);
  });

  test("los modelos guardan el periodo de las series en la URL", async ({ page }) => {
    await simularApi(page, { apagon: conResultados() });
    await page.goto("/apagon?desde=2026-12");
    await expect(page.getByRole("combobox", { name: "Desde" })).toHaveValue("2026-12");
    await expect(page.locator(".recharts-bar-rectangle")).toHaveCount(1);
    await page.getByRole("button", { name: /Restablecer filtros/ }).click();
    await expect(page).toHaveURL(/\/apagon$/);
  });
});

test.describe("Panel de tableros", () => {
  test("muestra los dos tableros y navega a cada uno", async ({ page }) => {
    await simularApi(page);
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1, name: "Tableros Analíticos" })).toBeVisible();
    await expect(page).toHaveTitle("Tableros Analíticos");

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
    await expect(page.locator("#panel .hs")).toHaveCount(10); // marcadores interactivos del panel: encabezado, introducción, 6 tableros, guía y pie
    await expect(page.locator("#dns-mapa .hs")).toHaveCount(10);
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

test.describe("Módulo de actualización", () => {
  test("acceso protegido, carga de un archivo, revisión, aplicación y cierre de sesión", async ({ page }) => {
    await simularApi(page);
    await page.goto("/actualizar");
    await expect(page.getByRole("form", { name: "Iniciar sesión" })).toBeVisible();
    await expect(page.getByText("1. Elige el tablero")).toHaveCount(0);

    await page.getByLabel("Usuario").fill("ana");
    await page.getByLabel("Contraseña").fill("incorrecta");
    await page.getByRole("button", { name: "Ingresar" }).click();
    await expect(page.getByRole("form", { name: "Iniciar sesión" }).getByRole("alert")).toContainText("Usuario o contraseña incorrectos");

    await page.getByLabel("Contraseña").fill("clave-correcta-2026");
    await page.getByRole("button", { name: "Ingresar" }).click();
    await page.getByRole("radio", { name: /Optimización/ }).check();
    await expect(page).toHaveURL(/tablero=optimizacion/);

    await page.getByLabel("Resumen de la corrida (JSON)", { exact: true }).setInputFiles({ name: "resumen.json", mimeType: "application/json", buffer: Buffer.from('{"a":1}') });
    await page.getByRole("button", { name: /Revisar archivos/ }).click();
    await expect(page.getByText("Los archivos son válidos")).toBeVisible();
    await expect(page.getByRole("button", { name: "Aplicar actualización" })).toBeDisabled();
    await page.getByRole("checkbox").check();
    await page.getByRole("button", { name: "Aplicar actualización" }).click();
    await expect(page.getByText("Tablero actualizado")).toBeVisible();
    await expect(page.getByRole("link", { name: "Ver el tablero" })).toHaveAttribute("href", "/optimizacion");

    await page.getByRole("button", { name: "Cerrar sesión" }).click();
    await expect(page.getByRole("form", { name: "Iniciar sesión" })).toBeVisible();
  });

  test("la página de actualización no tiene desplazamiento horizontal en celular", async ({ page }) => {
    await simularApi(page);
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/actualizar");
    await page.getByLabel("Usuario").fill("ana");
    await page.getByLabel("Contraseña").fill("clave-correcta-2026");
    await page.getByRole("button", { name: "Ingresar" }).click();
    await page.getByRole("radio", { name: /Gas/ }).check();
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
    await expect(page.getByRole("link", { name: /^Abrir el tablero de / })).toHaveCount(6);
    await expect(page.getByRole("link", { name: /^Guía del tablero de / })).toHaveCount(6);
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

  test("el visor de apagón: los controles piden otro escenario, viajan en la URL y no hay desplazamiento horizontal en celular", async ({ page }) => {
    const llamadas = await simularApi(page, {}, { escenariosApagon: true });
    await page.goto("/apagon");
    await expect(page.getByRole("heading", { level: 1, name: /Gemelo digital de riesgo de apagón/ })).toBeVisible();
    await expect(page.locator(".recharts-bar-rectangle").first()).toBeVisible();
    await page.getByRole("slider", { name: "ONI objetivo (°C)" }).fill("-1.5");
    await expect(page).toHaveURL(/oni=-1\.5/);
    await expect(page.getByLabel("Fase ENOS")).toContainText("La Niña moderada");
    await page.getByRole("radio", { name: /Pronóstico ENOS/ }).check();
    await expect(page.getByRole("slider", { name: "ONI objetivo (°C)" })).toHaveCount(0);
    await expect.poll(() => llamadas.filter((u) => u.pathname.endsWith("/apagon/escenario")).at(-1)?.searchParams.get("modo")).toBe("probabilistico");
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForLoadState("networkidle");
    const { ancho, visible } = await page.evaluate(() => ({ ancho: document.documentElement.scrollWidth, visible: window.innerWidth }));
    expect(ancho).toBeLessThanOrEqual(visible);
  });

  test("gas con resultados: el filtro de campo cambia el grafico y viaja en la URL", async ({ page }) => {
    await simularApi(page, { gas: conResultados(crearResultadoConDimensiones(), "gas") });
    await page.goto("/gas");
    await expect(page.getByRole("img", { name: /NACIONAL · Fiscalizado/ })).toBeVisible();
    await page.getByRole("combobox", { name: "Campo" }).selectOption("CUSIANA");
    await expect(page).toHaveURL(/serie=CUSIANA/);
    await expect(page.getByRole("img", { name: /CUSIANA · Fiscalizado/ })).toBeVisible();
    await page.goto("/gas?serie=NO_EXISTE");
    await expect(page.getByRole("combobox", { name: "Campo" })).toHaveValue("NACIONAL");
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
