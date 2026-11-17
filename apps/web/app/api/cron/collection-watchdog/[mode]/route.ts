import { hasValidCronSecret } from "@/features/automation/server/cron-auth";
import { isKoreanCollectionWeekday } from "@/features/automation/server/korean-schedule";
import {
  dispatchCollectionWatchdog,
  readGitHubDispatchSettings,
} from "@/features/automation/server/github-actions-dispatch";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request, { params }: { params: Promise<{ mode: string }> }) {
  if (!hasValidCronSecret(request, process.env.CRON_SECRET)) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  const { mode } = await params;
  if (mode !== "scheduled" && mode !== "press") {
    return Response.json({ error: "unknown collection mode" }, { status: 404 });
  }
  if (!isKoreanCollectionWeekday(new Date())) {
    return Response.json({ accepted: false, skipped: "WEEKEND" });
  }
  try {
    await dispatchCollectionWatchdog(readGitHubDispatchSettings(), mode);
    return Response.json({ accepted: true }, { status: 202 });
  } catch (error) {
    console.error("collection watchdog dispatch failed", error);
    return Response.json({ error: "백업 실행 확인 요청에 실패했습니다." }, { status: 500 });
  }
}
