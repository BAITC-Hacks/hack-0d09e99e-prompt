import {
  cleanText,
  findSkuIn,
  formatQty,
  formatSigned,
  metaFrom,
  modelFrom,
  peakSeasonFrom,
  supplierArticle,
  type OrderLine,
  type WorkspaceBundle,
} from "@/data/catalog";

function bundle(partial: Record<string, unknown>): WorkspaceBundle {
  return partial as unknown as WorkspaceBundle;
}

/** ru-KZ разделяет тысячи неразрывным пробелом — нормализуем для сравнения. */
const spaces = (s: string) => s.replace(/[\u00A0\u202F]/g, " ");

describe("cleanText", () => {
  it("схлопывает двойные пробелы и переводы строк из выгрузки 1С", () => {
    expect(cleanText("Кабель  ВВГнг\n 3х2,5")).toBe("Кабель ВВГнг 3х2,5");
  });

  it("тримит края", () => {
    expect(cleanText("  IEK  ")).toBe("IEK");
  });
});

describe("supplierArticle", () => {
  it("возвращает настоящий артикул поставщика", () => {
    expect(supplierArticle({ article: "AR-10-2-K01", code: "00-0001" })).toBe("AR-10-2-K01");
  });

  it("пустой артикул — пустая строка", () => {
    expect(supplierArticle({ article: "   ", code: "00-0001" })).toBe("");
  });

  it("артикул, совпавший с кодом 1С, не показываем", () => {
    expect(supplierArticle({ article: "00-0001", code: "00-0001" })).toBe("");
  });

  it("артикул с хвостом «_» — это код 1С, не показываем", () => {
    expect(supplierArticle({ article: "YND10-1600_", code: "00-0002" })).toBe("");
  });
});

describe("formatQty / formatSigned", () => {
  it("разбивает тысячи по-русски", () => {
    expect(spaces(formatQty(12345))).toBe("12 345");
  });

  it("не печатает лишних дробных знаков", () => {
    expect(formatQty(10)).toBe("10");
  });

  it("formatSigned: плюс, минус и ноль", () => {
    expect(formatSigned(5)).toBe("+5");
    expect(formatSigned(-3)).toBe("−3");
    expect(formatSigned(0)).toBe("0");
  });

  it("formatSigned: -0 не превращается в «+0»", () => {
    expect(formatSigned(-0)).toBe("0");
  });
});

describe("modelFrom", () => {
  it("переводит легаси-ключ target на русский", () => {
    const model = modelFrom(bundle({ model: { name: "m.cbm", target: "next_month_demand", policy: "forecast + 0.5*sigma" } }));
    expect(model.target).toBe("спрос на следующий месяц");
    expect(model.policy).toBe("прогноз + 0.5σ − остаток − в пути, кратно MOQ");
  });

  it("оставляет русские значения как есть", () => {
    const model = modelFrom(bundle({ model: { name: "m.cbm", target: "спрос", policy: "прогноз, кратно MOQ" } }));
    expect(model.target).toBe("спрос");
    expect(model.policy).toBe("прогноз, кратно MOQ");
  });

  it("без model в выгрузке отдаёт дефолты v2", () => {
    const model = modelFrom(bundle({}));
    expect(model.name).toBe("demand_model_v2.cbm");
    expect(model.label).toBe("CatBoost v2");
    expect(model.uses.length).toBeGreaterThan(0);
  });
});

describe("metaFrom", () => {
  it("подставляет пустые дефолты вместо undefined", () => {
    const meta = metaFrom(bundle({}));
    expect(meta.asOf).toBe("");
    expect(meta.horizonWeeks).toBe(0);
    expect(meta.seasonParts).toEqual([]);
  });

  it("прокидывает значения выгрузки", () => {
    const meta = metaFrom(bundle({ asOf: "2026-09-01", asOfLabel: "09.2026", supplier: "IEK" }));
    expect(meta.asOfLabel).toBe("09.2026");
    expect(meta.supplier).toBe("IEK");
  });
});

describe("findSkuIn", () => {
  const lines = [
    { article: "AR-1", code: "00-0001" },
    { article: "AR-2", code: "00-0002" },
  ] as OrderLine[];
  const b = bundle({ lines });

  it("находит по артикулу", () => {
    expect(findSkuIn(b, "AR-2")?.code).toBe("00-0002");
  });

  it("находит по коду 1С", () => {
    expect(findSkuIn(b, "00-0001")?.article).toBe("AR-1");
  });

  it("неизвестный ключ — undefined", () => {
    expect(findSkuIn(b, "нет-такого")).toBeUndefined();
  });
});

describe("peakSeasonFrom", () => {
  it("возвращает месяц с максимальным коэффициентом", () => {
    const peak = peakSeasonFrom(
      bundle({
        seasonParts: [
          { month: "сен", share: 0.1, coef: 1.0 },
          { month: "окт", share: 0.2, coef: 1.4 },
        ],
      }),
    );
    expect(peak?.month).toBe("окт");
  });

  it("без сезонности — null", () => {
    expect(peakSeasonFrom(bundle({}))).toBeNull();
  });
});
