import { render, screen, waitFor } from "@testing-library/react";
import { DirectorHome } from "@/components/DirectorHome";
import { useSession } from "@/components/SessionProvider";
import { useWorkspace } from "@/components/WorkspaceProvider";
import type { WorkspaceBundle } from "@/data/catalog";

jest.mock("@/components/SessionProvider", () => ({
  useSession: jest.fn(),
}));

jest.mock("@/components/WorkspaceProvider", () => ({
  useWorkspace: jest.fn(),
}));

const useSessionMock = useSession as jest.MockedFunction<typeof useSession>;
const useWorkspaceMock = useWorkspace as jest.MockedFunction<typeof useWorkspace>;
const logoutMock = jest.fn();
const fetchMock = jest.fn();

const bundle = {
  asOf: "2026-09-01",
  asOfLabel: "09.2026",
  supplier: "IEK",
  kpis: {
    toOrder: 390,
    critical: 316,
    deficit: 592,
    excess: 682,
    inboundSku: 284,
    inboundQty: 107720,
    skuTotal: 1200,
  },
} as unknown as WorkspaceBundle;

function mockOrder(order: unknown) {
  fetchMock.mockResolvedValue({ ok: true, json: async () => order });
}

beforeEach(() => {
  logoutMock.mockReset();
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  useSessionMock.mockReturnValue({
    user: { username: "daniyar", role: "director", name: "Данияр", title: "руководитель" },
    ready: true,
    login: jest.fn(),
    logout: logoutMock,
  });
  useWorkspaceMock.mockReturnValue({ bundle, setBundle: jest.fn() });
});

describe("DirectorHome", () => {
  it("шапка: имя, уведомления и факты выгрузки", async () => {
    mockOrder({ status: "draft" });
    render(<DirectorHome />);
    expect(screen.getByRole("heading", { name: "Уведомления" })).toBeInTheDocument();
    expect(screen.getByText(/Данияр/)).toBeInTheDocument();
    expect(screen.getByText("09.2026")).toBeInTheDocument();
    expect(screen.getByText("390")).toBeInTheDocument();
    expect(screen.getByText("316")).toBeInTheDocument();
    expect(await screen.findByText("Новых заказов нет")).toBeInTheDocument();
  });

  it("pending_approval: заказ ждёт решения, с кем и когда", async () => {
    mockOrder({ status: "pending_approval", sentBy: "Айгерим", sentAt: "2026-09-23T11:23:16Z" });
    render(<DirectorHome />);
    expect(await screen.findByText("Заказ ждёт вашего решения")).toBeInTheDocument();
    expect(screen.getByText(/Айгерим отправила заказ/)).toBeInTheDocument();
    expect(screen.getByText(/Поставщику ничего не ушло/)).toBeInTheDocument();
  });

  it("returned: показывает комментарий руководителя", async () => {
    mockOrder({ status: "returned", comment: "Уберите лишние позиции" });
    render(<DirectorHome />);
    expect(await screen.findByText("Заказ возвращён менеджеру")).toBeInTheDocument();
    expect(screen.getByText("Уберите лишние позиции")).toBeInTheDocument();
  });

  it("approved: карточка подтверждения", async () => {
    mockOrder({ status: "approved", decidedBy: "Данияр" });
    render(<DirectorHome />);
    expect(await screen.findByText("Заказ утверждён")).toBeInTheDocument();
    expect(screen.getByText(/Утвердил Данияр/)).toBeInTheDocument();
  });

  it("до ответа сервера — состояние проверки", () => {
    fetchMock.mockReturnValue(new Promise(() => undefined));
    render(<DirectorHome />);
    expect(screen.getByText("Проверяем, нет ли новых заказов…")).toBeInTheDocument();
  });

  it("кнопка «Выйти» зовёт logout", async () => {
    mockOrder({ status: "draft" });
    render(<DirectorHome />);
    screen.getByRole("button", { name: "Выйти" }).click();
    await waitFor(() => expect(logoutMock).toHaveBeenCalled());
  });
});
