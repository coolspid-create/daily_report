import { getPublicPressArchiveDate } from "@/features/public-feed/server/get-press-releases";

export const runtime = "nodejs";

interface RouteContext {
  params: Promise<{ date: string }>;
}

export async function GET(_: Request, { params }: RouteContext) {
  const { date } = await params;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return Response.json({ error: "올바른 발행일 형식이 아닙니다." }, { status: 400 });
  }

  try {
    const reports = await getPublicPressArchiveDate(date);
    return reports
      ? Response.json(reports)
      : Response.json({ error: "해당 발행일의 보도자료가 없습니다." }, { status: 404 });
  } catch {
    return Response.json({ error: "보도자료 발행본을 불러오지 못했습니다." }, { status: 500 });
  }
}
