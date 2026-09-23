import { expect, test } from "@playwright/test";
import { loginAs } from "./helpers";

test.beforeEach(async ({ page }) => {
  await loginAs(page, "aigerim", "buyer");
  await page.goto("/orders");
  await expect(page.getByRole("heading", { name: "Рекомендованные заказы" })).toBeVisible();
});

test("таблица рендерится: колонки и строки", async ({ page }) => {
  for (const col of ["Артикул", "Остаток", "В пути", "Прогноз", "Рек.", "Статус"]) {
    await expect(page.locator("th", { hasText: col }).first()).toBeVisible();
  }
  expect(await page.locator("tbody tr").count()).toBeGreaterThan(0);
});

test("строка раскрывается в объяснение расчёта", async ({ page }) => {
  await page.locator("button.expand").first().click();
  await expect(page.getByText(/^Почему/)).toBeVisible();
  await expect(page.getByText(/Прогноз — CatBoost на следующий месяц/)).toBeVisible();
});

test("поиск фильтрует строки", async ({ page }) => {
  await page.getByPlaceholder("Название, артикул IEK или код 1С").fill("zzz-ничего-не-найдёт");
  await expect(page.getByText(/Показано/)).toContainText("0 из 0");
});

test("количество не кратное MOQ блокирует согласование", async ({ page }) => {
  const qtyInputs = page.locator("input.qty");
  const count = await qtyInputs.count();
  let target: { index: number; step: number } | null = null;
  for (let i = 0; i < count; i += 1) {
    const step = Number(await qtyInputs.nth(i).getAttribute("step"));
    if (step > 1) {
      target = { index: i, step };
      break;
    }
  }
  test.skip(!target, "в видимых строках нет MOQ больше 1");
  await qtyInputs.nth(target!.index).fill(String(target!.step + 1));
  await expect(page.getByText(/поз\. с количеством не кратным MOQ/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Отправить на согласование|На согласовании/ }),
  ).toBeDisabled();
});
