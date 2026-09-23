import { expect, test } from "@playwright/test";
import { loginAs } from "./helpers";

test("гость видит экран входа с демо-доступом", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
  await expect(page.getByText("Демо-доступ")).toBeVisible();
  await expect(page.getByText("Айгерим")).toBeVisible();
  await expect(page.getByText("Данияр")).toBeVisible();
});

test("байер входит и видит стол закупа", async ({ page }) => {
  await loginAs(page, "aigerim", "buyer");
  await expect(page.getByRole("link", { name: /Заказы поставщикам/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "Дашборд" })).toBeVisible();
});

test("неверный пароль — ошибка, остаёмся на экране входа", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel(/Логин/).fill("aigerim");
  await page.getByLabel(/Пароль/).fill("не-тот-пароль");
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.getByText("Неверный логин или пароль")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
});

test("выход возвращает на экран входа", async ({ page }) => {
  await loginAs(page, "aigerim", "buyer");
  await page.getByRole("button", { name: "Выйти" }).click();
  await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
});
