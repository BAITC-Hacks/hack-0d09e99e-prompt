type LogoProps = {
  className?: string;
  title?: string;
};

/** Векторный знак Q. Цвет — currentColor, в UI задаём text-primary. Пустой title прячет имя, если рядом уже написано «Qor». */
export function Logo({ className = "h-8 w-8", title = "Qor" }: LogoProps) {
  const named = title.length > 0;
  return (
    <svg viewBox="0 0 64 64" className={className} role={named ? "img" : undefined} aria-label={named ? title : undefined} aria-hidden={named ? undefined : true}>
      {named ? <title>{title}</title> : null}
      <circle cx="30" cy="29" r="16" fill="none" stroke="currentColor" strokeWidth="7" />
      <path d="M40.5 39.5 L51 52" stroke="currentColor" strokeWidth="7" strokeLinecap="round" />
    </svg>
  );
}
