type IconProps = {
  name: string;
  className?: string;
  filled?: boolean;
};

export function Icon({ name, className = "", filled = false }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      aria-hidden
      style={filled ? { fontVariationSettings: "'FILL' 1, 'wght' 500" } : undefined}
    >
      {name}
    </span>
  );
}
