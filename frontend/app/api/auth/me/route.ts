import { authToken, qorError, qorFetch } from "@/server/qor";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const token = await authToken();
  if (!token) return Response.json({ error: "Нет входа" }, { status: 401 });
  const { ok, status, data } = await qorFetch("/v1/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!ok) return Response.json({ error: qorError(data, "Сессия истекла") }, { status });
  return Response.json(data);
}
