import { getWorkspace } from "@/server/workspace";

export const dynamic = "force-dynamic";

export function GET() {
  return getWorkspace();
}
