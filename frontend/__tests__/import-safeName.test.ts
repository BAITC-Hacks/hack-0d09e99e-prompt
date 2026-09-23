import path from "path";
import { safeName } from "@/server/upload-name";

describe("safeName", () => {
  it("пропускает нормальные выгрузки 1С", () => {
    expect(safeName("MOQ  ИЭК.xlsx")).toBe("MOQ  ИЭК.xlsx");
    expect(safeName("Путь ИЭК 22.09.2026.xlsx")).toBe("Путь ИЭК 22.09.2026.xlsx");
    expect(safeName("old.xls")).toBe("old.xls");
  });

  it("никогда не выпускает результат за пределы папки загрузок", () => {
    const evil = [
      "../../../backend/run_workspace.py",
      "../../../../etc/passwd",
      "..\\..\\backend\\qor\\pipeline.py",
      "/etc/hosts",
      "../../backend/run_workspace.xlsx",
    ];
    for (const name of evil) {
      const out = safeName(name);
      if (out === null) continue;
      expect(out).not.toContain("..");
      expect(out).not.toContain("/");
      expect(path.join("/uploads", out).startsWith("/uploads/")).toBe(true);
    }
  });

  it("отвергает не-Excel", () => {
    expect(safeName("../../../backend/run_workspace.py")).toBeNull();
    expect(safeName("shell.sh")).toBeNull();
    expect(safeName("")).toBeNull();
    expect(safeName("...")).toBeNull();
    expect(safeName("evil.xlsx.py")).toBeNull();
  });

  it("обезвреживает путь, замаскированный под xlsx", () => {
    expect(safeName("../../backend/run_workspace.xlsx")).toBe("run_workspace.xlsx");
  });
});
