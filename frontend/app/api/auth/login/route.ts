import { cookies } from "next/headers";
import { qorError, qorFetch } from "@/server/qor";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body?.username || !body?.password) {
    return Response.json({ error: "Введите логин и пароль" }, { status: 400 });
  }
  const { ok, status, data } = await qorFetch("/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: body.username, password: body.password }),
  });
  const token = data.token;
  if (!ok || typeof token !== "string") {
    return Response.json({ error: qorError(data, "Неверный логин или пароль") }, { status: status || 401 });
  }
  (await cookies()).set("qor_token", token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  return Response.json({
    username: data.username,
    role: data.role,
    name: data.name,
    title: data.title,
  });
}
