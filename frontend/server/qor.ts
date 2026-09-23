import { cookies } from "next/headers";

const API = process.env.QOR_API ?? "http://127.0.0.1:8000";

export async function authToken() {
  return (await cookies()).get("qor_token")?.value;
}

export async function qorFetch(path: string, init: RequestInit = {}) {
  try {
    const res = await fetch(`${API}${path}`, { ...init, cache: "no-store" });
    const data = (await res.json().catch(() => ({}))) as Record<string, unknown> & { detail?: string };
    return { ok: res.ok, status: res.status, data };
  } catch {
    return { ok: false, status: 503, data: { detail: "Сервер расчёта не запущен (порт 8000)" } };
  }
}

export function qorError(data: { detail?: unknown }, fallback: string) {
  return typeof data.detail === "string" ? data.detail : fallback;
}
