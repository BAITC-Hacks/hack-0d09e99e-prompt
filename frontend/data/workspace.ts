import { existsSync, readFileSync } from "fs";
import path from "path";
import type { WorkspaceBundle } from "./catalog";

const BACKEND_DATA = path.join(process.cwd(), "..", "backend", "data");

export const WORKSPACE_PATH = path.join(BACKEND_DATA, "workspace.json");
export const UPLOAD_DIR = path.join(BACKEND_DATA, "uploads");

export function readWorkspace(): WorkspaceBundle | null {
  if (!existsSync(WORKSPACE_PATH)) return null;
  return JSON.parse(readFileSync(WORKSPACE_PATH, "utf8")) as WorkspaceBundle;
}
