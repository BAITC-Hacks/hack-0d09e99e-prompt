"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";

type Msg = { text: string; mine: boolean };

type Block =
  | { kind: "text"; text: string }
  | { kind: "list"; items: string[] }
  | { kind: "table"; headers: string[]; rows: string[][] };

function splitRow(line: string) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function isSeparator(line: string) {
  return /^\|?[\s|:-]+\|?$/.test(line.trim()) && line.includes("-");
}

function isBullet(line: string) {
  return /^[-•]\s+/.test(line.trim());
}

/** Инлайн-разметка модели: **жирный** и `код`. */
function inline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

/** Текст ответа, списки и markdown-таблицы модели — отдельными блоками, чтобы ничего не склеивалось в узкой панели. */
function blocksOf(text: string): Block[] {
  const lines = text.split("\n");
  const blocks: Block[] = [];
  const prose: string[] = [];
  const list: string[] = [];
  const flushProse = () => {
    const text = prose.join(" ").trim();
    if (text) blocks.push({ kind: "text", text });
    prose.length = 0;
  };
  const flushList = () => {
    if (list.length) blocks.push({ kind: "list", items: [...list] });
    list.length = 0;
  };
  const flush = () => {
    flushProse();
    flushList();
  };

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const next = lines[i + 1];
    if (line.trim().startsWith("|") && next !== undefined && isSeparator(next)) {
      flush();
      const headers = splitRow(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        rows.push(splitRow(lines[i]));
        i += 1;
      }
      blocks.push({ kind: "table", headers, rows });
    } else if (isBullet(line)) {
      flushProse();
      list.push(line.trim().replace(/^[-•]\s+/, ""));
      i += 1;
    } else if (!line.trim()) {
      flush();
      i += 1;
    } else {
      flushList();
      prose.push(line.trim());
      i += 1;
    }
  }
  flush();
  return blocks;
}

function MessageBody({ text }: { text: string }) {
  return (
    <>
      {blocksOf(text).map((block, i) => {
        if (block.kind === "text") return <p key={i}>{inline(block.text)}</p>;
        if (block.kind === "list") {
          return (
            <ul key={i} className="chat-list">
              {block.items.map((item, li) => (
                <li key={li}>{inline(item)}</li>
              ))}
            </ul>
          );
        }
        return (
          <div key={i} className="chat-table-wrap">
            <table>
              <thead>
                <tr>
                  {block.headers.map((header) => (
                    <th key={header} scope="col">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {block.rows.map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td key={ci}>{inline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </>
  );
}

const SUGGESTIONS = [
  "Что критично заказать?",
  "Позиции по поставщику IEK",
  "Что будет, если заказать 130300791_ вдвое больше?",
];

/** Маленький чат с AI-ассистентом в правом нижнем углу. */
export function AssistantChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fieldRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, thinking, open]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || thinking) return;
    setInput("");
    if (fieldRef.current) fieldRef.current.style.height = "auto";
    setMessages((prev) => [...prev, { text: question, mine: true }]);
    setThinking(true);
    let answer: string;
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      const data = (await res.json().catch(() => ({}))) as { answer?: string; error?: string };
      answer = res.ok && data.answer ? data.answer : data.error ?? "Ассистент не ответил";
    } catch {
      answer = "Не удалось связаться с ассистентом";
    }
    setMessages((prev) => [...prev, { text: answer, mine: false }]);
    setThinking(false);
    fieldRef.current?.focus();
  }

  return (
    <>
      <section
        className={open ? "assistant-panel open" : "assistant-panel"}
        role="dialog"
        aria-label="AI-ассистент"
        aria-hidden={!open}
      >
          <header>
            <div>
              <p className="caps">AI-ассистент</p>
              <h2>Спросить о заказе</h2>
            </div>
            <button type="button" onClick={() => setOpen(false)} className="icon-btn" aria-label="Закрыть">
              <Icon name="close" />
            </button>
          </header>

          <div className="chat-log" ref={scrollRef}>
            <div className="bubble">
              Отвечаю только по данным расчёта Qor: прогноз, остатки, путь, MOQ и риски.
              Заказ поставщику не отправляю.
            </div>
            {messages.map((m, i) => (
              <div key={i} className={m.mine ? "bubble mine" : "bubble"}>
                <MessageBody text={m.text} />
              </div>
            ))}
            {thinking ? (
              <div className="bubble thinking" aria-live="polite">
                <span className="chat-dots" aria-hidden>
                  <i />
                  <i />
                  <i />
                </span>
                <span className="skip">Ассистент считает</span>
              </div>
            ) : null}
          </div>

          {messages.length === 0 ? (
            <div className="chat-suggest">
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" onClick={() => void send(s)}>
                  {s}
                </button>
              ))}
            </div>
          ) : null}

          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              void send(input);
            }}
          >
            <textarea
              ref={fieldRef}
              rows={1}
              value={input}
              disabled={thinking}
              placeholder={thinking ? "Ассистент считает…" : "Спросить ассистента…"}
              aria-label="Вопрос ассистенту"
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = `${Math.min(e.target.scrollHeight, 112)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send(input);
                }
              }}
            />
            <button type="submit" className="btn btn-accent" disabled={thinking || !input.trim()} aria-label="Отправить">
              <Icon name="arrow_upward" />
            </button>
          </form>
        </section>

      <button
        type="button"
        className="assistant-fab"
        onClick={() => setOpen((v) => !v)}
        aria-label="Ассистент"
        aria-expanded={open}
      >
        <span className="fab-icon">
          <Icon name="chat" filled />
          <Icon name="keyboard_arrow_down" />
        </span>
      </button>
    </>
  );
}
