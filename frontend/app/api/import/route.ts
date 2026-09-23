import { importWorkspace } from "@/server/import";

export const runtime = "nodejs";
export const maxDuration = 120;

export function POST(req: Request) {
  return importWorkspace(req);
}
