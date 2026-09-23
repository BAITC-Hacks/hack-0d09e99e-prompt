import { expect, test } from "@playwright/test";
import { apiOrderStatus, apiReturn, apiToken, loginAs } from "./helpers";

// Полный круг согласования на живом демо-стенде. Тест адаптивен к текущему
// статусу и всегда оставляет заказ в «на согласовании» — прогоняемо повторно.
test("круг согласования: отправка → возврат с комментарием → повторная отправка", async ({
  page,
  request,
}) => {
  const buyer = await apiToken(request, "aigerim", "buyer");
  const director = await apiToken(request, "daniyar", "director");
  const initial = await apiOrderStatus(request, buyer);
  test.skip(initial === "approved", "заказ уже утверждён — круг невозможен без новой выгрузки");

  // Если заказ висит на согласовании — директор возвращает его в работу.
  if (initial === "pending_approval") {
    await apiReturn(request, director, "e2e: возврат перед прогоном");
  }

  // Байер отправляет заказ через UI.
  await loginAs(page, "aigerim", "buyer");
  await page.goto("/orders");
  const submit = page.getByRole("button", { name: "Отправить на согласование" });
  await expect(submit).toBeEnabled();
  await submit.click();
  await expect(page.getByRole("button", { name: "На согласовании" })).toBeDisabled();
  await expect(page.locator(".summary")).toContainText("На согласовании");

  // Директор видит карточку в своих уведомлениях.
  await page.getByRole("button", { name: "Выйти" }).click();
  await loginAs(page, "daniyar", "director");
  await expect(page.getByText("Заказ ждёт вашего решения")).toBeVisible();

  // Решение директор принимает в приложении — здесь возвращаем через API.
  await apiReturn(request, director, "e2e: проверка возврата");

  // Байер видит возврат и комментарий руководителя.
  await page.getByRole("button", { name: "Выйти" }).click();
  await loginAs(page, "aigerim", "buyer");
  await page.goto("/orders");
  await expect(page.locator(".summary")).toContainText("На доработке");
  await expect(page.getByText(/e2e: проверка возврата/)).toBeVisible();

  // И отправляет снова: заказ заканчивает прогон в статусе «на согласовании».
  await page.getByRole("button", { name: "Отправить на согласование" }).click();
  await expect(page.locator(".summary")).toContainText("На согласовании");
  expect(await apiOrderStatus(request, buyer)).toBe("pending_approval");
});
