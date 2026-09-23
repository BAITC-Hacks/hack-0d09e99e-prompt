import { NextResponse } from "next/server";
import { readWorkspace } from "@/data/workspace";

export function getWorkspace() {
  return NextResponse.json({ bundle: readWorkspace() });
}
