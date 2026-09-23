type LogoProps = {
  title?: string;
};

/** Векторный знак Q. Цвет берётся от родителя. */
export function Logo({ title = "Qor" }: LogoProps) {
  const named = title.length > 0;
  return (
    <svg viewBox="0 0 64 64" role={named ? "img" : undefined} aria-label={named ? title : undefined} aria-hidden={named ? undefined : true}>
      {named ? <title>{title}</title> : null}
      <circle cx="30" cy="29" r="16" fill="none" stroke="currentColor" strokeWidth="7" />
      <path d="M40.5 39.5 L51 52" stroke="currentColor" strokeWidth="7" strokeLinecap="round" />
    </svg>
  );
}
