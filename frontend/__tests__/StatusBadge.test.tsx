import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/StatusBadge";

describe("StatusBadge", () => {
  it("подписывает каждый тон по-русски", () => {
    render(
      <>
        <StatusBadge tone="critical" />
        <StatusBadge tone="warning" />
        <StatusBadge tone="safe" />
      </>,
    );
    expect(screen.getByText("Критично")).toBeInTheDocument();
    expect(screen.getByText("Скоро")).toBeInTheDocument();
    expect(screen.getByText("Норма")).toBeInTheDocument();
  });

  it("проставляет data-tone для цвета", () => {
    render(<StatusBadge tone="critical" />);
    expect(screen.getByText("Критично")).toHaveAttribute("data-tone", "critical");
  });

  it("пульс включается только флагом", () => {
    const { rerender } = render(<StatusBadge tone="critical" />);
    expect(screen.getByText("Критично")).not.toHaveAttribute("data-pulse");
    rerender(<StatusBadge tone="critical" pulse />);
    expect(screen.getByText("Критично")).toHaveAttribute("data-pulse", "true");
  });
});
