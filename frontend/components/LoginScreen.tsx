"use client";

import { useState } from "react";
import { Logo } from "./Logo";
import { useSession } from "./SessionProvider";

const accounts = [
  { username: "aigerim", password: "buyer", who: "Айгерим · менеджер закупа" },
  { username: "daniyar", password: "director", who: "Данияр · руководитель" },
];

export function LoginScreen() {
  const { login } = useSession();
  const [username, setUsername] = useState("aigerim");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось войти");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="gate">
      <section className="card login">
        <div className="login-brand">
          <span className="login-mark">
            <Logo title="" />
          </span>
          <div>
            <strong>Qor</strong>
            <p className="muted">Закупки по выгрузке 1С · ekt.kz</p>
          </div>
        </div>
        <h1>Вход</h1>
        <p className="lede">
          Сайт — стол закупщика: выгрузка 1С, количество, отправка на согласование. Утверждает руководитель, у него отдельный вход.
        </p>
        <form onSubmit={(event) => void submit(event)}>
          <label className="field">
            <span>Логин</span>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
          </label>
          <label className="field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Входим…" : "Войти"}
          </button>
        </form>
        {error ? <p className="error">{error}</p> : null}
        <div className="login-demo">
          <p className="caps">Демо-доступ</p>
          <ul className="accounts">
            {accounts.map((account) => (
              <li key={account.username}>
                <button
                  type="button"
                  className={username === account.username ? "active" : undefined}
                  onClick={() => {
                    setUsername(account.username);
                    setPassword(account.password);
                  }}
                >
                  <span className="avatar" aria-hidden>{account.who.charAt(0)}</span>
                  <span>
                    <strong>{account.who.split(" · ")[0]}</strong>
                    <span>{account.who.split(" · ")[1]}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
