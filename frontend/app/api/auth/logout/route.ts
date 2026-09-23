import { cookies } from "next/headers";

export const runtime = "nodejs";

export async function POST() {
  (await cookies()).delete("qor_token");
  return Response.json({ ok: true });
}
