type IconProps = {
  name: string;
  filled?: boolean;
};

export function Icon({ name, filled = false }: IconProps) {
  return (
    <span
      className="material-symbols-outlined"
      aria-hidden
      style={filled ? { fontVariationSettings: "'FILL' 1, 'wght' 500" } : undefined}
    >
      {name}
    </span>
  );
}
