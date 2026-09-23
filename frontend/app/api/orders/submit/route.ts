import { authToken, qorError, qorFetch } from "@/server/qor";

export const runtime = "nodejs";

export async function POST() {
  const token = await authToken();
  if (!token) return Response.json({ error: "Нет входа" }, { status: 401 });
  const { ok, status, data } = await qorFetch("/v1/orders/iek-current/submit", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!ok) return Response.json({ error: qorError(data, "Не удалось отправить") }, { status });
  return Response.json(data);
}
