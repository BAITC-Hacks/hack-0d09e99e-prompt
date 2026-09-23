import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const API = process.env.QOR_API ?? "http://127.0.0.1:8000";
export const ORDER_ID = "iek-current";

/** Вход через форму (тот же путь, что у пользователя). */
export async function loginAs(page: Page, username: string, password: string) {
  await page.goto("/");
  await page.getByLabel(/Логин/).fill(username);
  await page.getByLabel(/Пароль/).fill(password);
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.getByRole("heading", { name: "Вход" })).toBeHidden();
}

/** Токен API без UI — для подготовки и проверки состояния. */
export async function apiToken(request: APIRequestContext, username: string, password: string) {
  const res = await request.post(`${API}/v1/auth/login`, { data: { username, password } });
  if (!res.ok()) throw new Error(`API login ${username}: ${res.status()}`);
  return ((await res.json()) as { token: string }).token;
}

export async function apiOrderStatus(request: APIRequestContext, token: string) {
  const res = await request.get(`${API}/v1/orders/current`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok()) throw new Error(`orders/current: ${res.status()}`);
  return ((await res.json()) as { status: string }).status;
}

export async function apiReturn(request: APIRequestContext, directorToken: string, comment: string) {
  const res = await request.post(`${API}/v1/orders/${ORDER_ID}/return`, {
    headers: { Authorization: `Bearer ${directorToken}` },
    data: { comment },
  });
  if (!res.ok()) throw new Error(`return: ${res.status()}`);
}
