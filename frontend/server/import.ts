import { execFile } from "child_process";
import { mkdir, writeFile } from "fs/promises";
import { promisify } from "util";
import { NextResponse } from "next/server";
import path from "path";
import { readWorkspace, UPLOAD_DIR, WORKSPACE_PATH } from "@/data/workspace";

const exec = promisify(execFile);

async function importViaApi(req: Request, api: string) {
  const demo = new URL(req.url).searchParams.get("demo") === "1";
  let body: FormData | undefined;
  if (!demo) {
    const incoming = await req.formData();
    const files = incoming.getAll("files").filter((f): f is File => f instanceof File);
    if (!files.length) {
      return NextResponse.json({ error: "Загрузите выгрузки 1С (xlsx)" }, { status: 400 });
    }
    body = new FormData();
    for (const file of files) body.append("files", file, file.name);
  }
  try {
    const res = await fetch(`${api}/v1/workspace${demo ? "?demo=1" : ""}`, { method: "POST", body });
    const data = (await res.json().catch(() => ({}))) as { detail?: unknown };
    if (!res.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "ошибка расчёта";
      return NextResponse.json({ error: detail }, { status: res.status });
    }
    return NextResponse.json({ bundle: data });
  } catch {
    return NextResponse.json({ error: "Сервер расчёта не запущен" }, { status: 503 });
  }
}

export async function importWorkspace(req: Request) {
  const api = process.env.QOR_API;
  if (api) return importViaApi(req, api);
  const url = new URL(req.url);
  const demo = url.searchParams.get("demo") === "1";

  const script = path.join(process.cwd(), "..", "backend", "run_workspace.py");
  const env = {
    ...process.env,
    QOR_OUT: WORKSPACE_PATH,
    IEK_DATA_DIR: demo ? process.env.IEK_DATA_DIR || "/Users/azamatomirtaj/Documents/IEK" : UPLOAD_DIR,
  };

  if (!demo) {
    const form = await req.formData();
    const files = form.getAll("files").filter((f): f is File => f instanceof File);
    if (!files.length) {
      return NextResponse.json({ error: "Загрузите выгрузки 1С (xlsx)" }, { status: 400 });
    }
    await mkdir(UPLOAD_DIR, { recursive: true });
    for (const file of files) {
      const buf = Buffer.from(await file.arrayBuffer());
      await writeFile(path.join(UPLOAD_DIR, file.name), buf);
    }
  }

  try {
    await exec("python3", [script], { env, cwd: path.join(process.cwd(), "..", "backend") });
  } catch (err) {
    const message = err instanceof Error ? err.message : "ошибка расчёта";
    return NextResponse.json({ error: message }, { status: 500 });
  }

  return NextResponse.json({ bundle: readWorkspace() });
}
