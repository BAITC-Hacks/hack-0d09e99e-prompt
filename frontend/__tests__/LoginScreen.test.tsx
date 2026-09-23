import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { LoginScreen } from "@/components/LoginScreen";
import { useSession } from "@/components/SessionProvider";

jest.mock("@/components/SessionProvider", () => ({
  useSession: jest.fn(),
}));

const useSessionMock = useSession as jest.MockedFunction<typeof useSession>;
const loginMock = jest.fn();

beforeEach(() => {
  loginMock.mockReset();
  loginMock.mockResolvedValue(undefined);
  useSessionMock.mockReturnValue({
    user: null,
    ready: true,
    login: loginMock,
    logout: jest.fn(),
  });
});

describe("LoginScreen", () => {
  it("показывает бренд и оба демо-аккаунта", () => {
    render(<LoginScreen />);
    expect(screen.getByRole("heading", { name: "Вход" })).toBeInTheDocument();
    expect(screen.getByText("Айгерим")).toBeInTheDocument();
    expect(screen.getByText("Данияр")).toBeInTheDocument();
  });

  it("клик по аккаунту подставляет логин и пароль", () => {
    render(<LoginScreen />);
    fireEvent.click(screen.getByText("Данияр"));
    expect(screen.getByLabelText(/Логин/)).toHaveValue("daniyar");
    expect(screen.getByLabelText(/Пароль/)).toHaveValue("director");
  });

  it("выбранный аккаунт подсвечен", () => {
    render(<LoginScreen />);
    const daniyar = screen.getByText("Данияр").closest("button")!;
    expect(daniyar).not.toHaveClass("active");
    fireEvent.click(daniyar);
    expect(daniyar).toHaveClass("active");
  });

  it("submit зовёт login с введёнными данными", async () => {
    render(<LoginScreen />);
    fireEvent.change(screen.getByLabelText(/Логин/), { target: { value: "aigerim" } });
    fireEvent.change(screen.getByLabelText(/Пароль/), { target: { value: "buyer" } });
    fireEvent.click(screen.getByRole("button", { name: "Войти" }));
    await waitFor(() => expect(loginMock).toHaveBeenCalledWith("aigerim", "buyer"));
  });

  it("ошибка входа показывается текстом", async () => {
    loginMock.mockRejectedValue(new Error("Неверный логин или пароль"));
    render(<LoginScreen />);
    fireEvent.change(screen.getByLabelText(/Пароль/), { target: { value: "buyer" } });
    fireEvent.click(screen.getByRole("button", { name: "Войти" }));
    expect(await screen.findByText("Неверный логин или пароль")).toBeInTheDocument();
  });
});
