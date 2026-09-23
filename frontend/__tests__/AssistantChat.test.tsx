import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AssistantChat } from "@/components/AssistantChat";

const fetchMock = jest.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
});

function openChat() {
  render(<AssistantChat />);
  fireEvent.click(screen.getByRole("button", { name: "Ассистент" }));
}

describe("AssistantChat", () => {
  it("свернут: только круглая кнопка, без панели", () => {
    render(<AssistantChat />);
    expect(screen.getByRole("button", { name: "Ассистент" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("кнопка открывает и закрывает панель", () => {
    render(<AssistantChat />);
    const fab = screen.getByRole("button", { name: "Ассистент" });
    fireEvent.click(fab);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Закрыть" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("отправляет вопрос в /api/chat и показывает ответ", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "Критично 3 позиции IEK." }),
    });

    openChat();
    fireEvent.change(screen.getByLabelText("Вопрос ассистенту"), { target: { value: "Что срочно заказать?" } });
    fireEvent.click(screen.getByRole("button", { name: "Отправить" }));

    expect(await screen.findByText("Критично 3 позиции IEK.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/chat", expect.objectContaining({ method: "POST" }));
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body.message).toBe("Что срочно заказать?");
  });

  it("подсказка отправляется как вопрос", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "Ответ" }),
    });

    openChat();
    fireEvent.click(screen.getByRole("button", { name: "Что критично заказать?" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body.message).toBe("Что критично заказать?");
  });

  it("Enter отправляет вопрос, Shift+Enter — нет", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "Ок" }),
    });

    openChat();
    const field = screen.getByLabelText("Вопрос ассистенту");
    fireEvent.change(field, { target: { value: "Почему 3550?" } });
    fireEvent.keyDown(field, { key: "Enter", shiftKey: true });
    expect(fetchMock).not.toHaveBeenCalled();

    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body.message).toBe("Почему 3550?");
  });

  it("markdown-таблицу в ответе показывает как таблицу", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        answer: "Критично:\n| SKU | Остаток |\n| --- | --- |\n| 130300792_ | 0 |",
      }),
    });

    openChat();
    fireEvent.change(screen.getByLabelText("Вопрос ассистенту"), { target: { value: "Что критично?" } });
    fireEvent.click(screen.getByRole("button", { name: "Отправить" }));

    expect(await screen.findByRole("cell", { name: "130300792_" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Остаток" })).toBeInTheDocument();
    expect(screen.queryByText(/\| SKU/)).not.toBeInTheDocument();
  });

  it("ошибка сервиса показывается текстом", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ error: "AI-ассистент не запущен (порт 8001)" }),
    });

    openChat();
    fireEvent.change(screen.getByLabelText("Вопрос ассистенту"), { target: { value: "hi" } });
    fireEvent.click(screen.getByRole("button", { name: "Отправить" }));

    expect(await screen.findByText("AI-ассистент не запущен (порт 8001)")).toBeInTheDocument();
  });
});
