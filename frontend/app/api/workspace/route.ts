import { NextResponse } from "next/server";
import { readWorkspace } from "@/app/data/workspace";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({ bundle: readWorkspace() });
}
