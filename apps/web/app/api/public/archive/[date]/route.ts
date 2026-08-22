import { getPublicArchiveSnapshot } from "@/features/public-feed/server/get-public-snapshots";

export const runtime = "nodejs";

interface RouteContext {
  params: Promise<{ date: string }>;
}

export async function GET(_: Request, { params }: RouteContext) {
  const { date } = await params;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return Response.json({ error: "invalid date" }, { status: 400 });
  }
  try {
    const snapshot = await getPublicArchiveSnapshot(date);
    return snapshot
      ? Response.json(snapshot)
      : Response.json({ error: "not found" }, { status: 404 });
  } catch (error) {
    console.error("public archive snapshot load failed", error);
    return Response.json({ error: "발행본을 불러오지 못했습니다." }, { status: 500 });
  }
}
