import path from "path";

/**
 * Имя загружаемого файла приходит из Content-Disposition и управляется
 * отправителем. Без basename `../../../backend/run_workspace.py` вышел бы
 * за пределы папки загрузок — а этот скрипт затем запускается через execFile.
 *
 * Возвращает безопасное имя или null, если файл принимать нельзя.
 */
export function safeName(raw: string): string | null {
  const name = path.basename(raw).replace(/^\.+/, "").trim();
  if (!name || !/^[^/\\]+\.xlsx?$/i.test(name)) return null;
  return name;
}
