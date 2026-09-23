import { expect, test } from "@playwright/test";
import { loginAs } from "./helpers";

test("директор видит уведомления, а не стол закупа", async ({ page }) => {
  await loginAs(page, "daniyar", "director");

  await expect(page.getByRole("heading", { name: "Уведомления" })).toBeVisible();
  await expect(page.getByText(/Данияр/)).toBeVisible();

  // факты выгрузки
  await expect(page.getByText("Выгрузка")).toBeVisible();
  await expect(page.getByText("Позиций в заказе")).toBeVisible();
  await expect(page.getByText("Критично")).toBeVisible();
  await expect(page.getByText("В пути")).toBeVisible();

  // статусная карточка — один из четырёх заголовков
  await expect(
    page.getByText(/Новых заказов нет|Заказ ждёт вашего решения|Заказ утверждён|Заказ возвращён менеджеру/),
  ).toBeVisible();

  // навигации и настроек байера у директора нет
  await expect(page.getByRole("link", { name: /Заказы поставщикам/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Как считает/ })).toHaveCount(0);
});
