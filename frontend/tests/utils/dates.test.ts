import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { aISO, fechaHaceDias, hoyISO } from "@/lib/utils/dates";

// El usuario objetivo esta en Colombia (UTC-5, sin horario de verano).
const TZ_ORIGINAL = process.env.TZ;

beforeEach(() => {
  process.env.TZ = "America/Bogota";
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  if (TZ_ORIGINAL === undefined) delete process.env.TZ;
  else process.env.TZ = TZ_ORIGINAL;
});

describe("fechas locales", () => {
  it("hoyISO devuelve el dia local a media manana", () => {
    vi.setSystemTime(new Date("2026-09-23T15:00:00Z")); // 10:00 en Bogota
    expect(hoyISO()).toBe("2026-09-23");
  });

  it("hoyISO sigue siendo el dia local por la noche, aunque en UTC ya sea manana", () => {
    vi.setSystemTime(new Date("2026-09-24T02:30:00Z")); // 21:30 del 23 en Bogota
    expect(hoyISO()).toBe("2026-09-23");
  });

  it("hoyISO no se adelanta un dia a las 19:00 locales (00:00 UTC)", () => {
    vi.setSystemTime(new Date("2026-09-24T00:00:00Z")); // 19:00 del 23 en Bogota
    expect(hoyISO()).toBe("2026-09-23");
  });

  it("fechaHaceDias resta dias del calendario local", () => {
    vi.setSystemTime(new Date("2026-09-24T02:30:00Z")); // 21:30 del 23 en Bogota
    expect(fechaHaceDias(180)).toBe("2026-03-27");
    expect(fechaHaceDias(0)).toBe("2026-09-23");
  });

  it("fechaHaceDias cruza cambios de mes y de anio", () => {
    vi.setSystemTime(new Date("2026-01-03T15:00:00Z"));
    expect(fechaHaceDias(5)).toBe("2025-12-29");
  });

  it("aISO formatea con ceros a la izquierda", () => {
    expect(aISO(new Date(2026, 0, 5))).toBe("2026-01-05");
  });
});
