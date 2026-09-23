import { SkuScreen } from "@/screens/Sku";

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return <SkuScreen code={code} />;
}
