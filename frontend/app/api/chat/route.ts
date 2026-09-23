import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const AI = process.env.QOR_AI_API ?? "http://127.0.0.1:8001";

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as { message?: string };
  const message = body.message?.trim();
  if (!message) {
    return NextResponse.json({ error: "Пустой вопрос" }, { status: 400 });
  }
  try {
    const res = await fetch(`${AI}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      cache: "no-store",
    });
    const data = (await res.json().catch(() => ({}))) as { answer?: string; detail?: string };
    if (!res.ok) {
      return NextResponse.json({ error: data.detail ?? "Ассистент не ответил" }, { status: res.status });
    }
    return NextResponse.json({ answer: data.answer ?? "" });
  } catch {
    return NextResponse.json({ error: "AI-ассистент не запущен (порт 8001)" }, { status: 503 });
  }
}
