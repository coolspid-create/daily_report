import { hasValidCronSecret } from "@/features/automation/server/cron-auth";
import { isKoreanCollectionWeekday } from "@/features/automation/server/korean-schedule";
import {
  dispatchCollectionWatchdog,
  dispatchCollectorWorkflow,
  readGitHubDispatchSettings,
} from "@/features/automation/server/github-actions-dispatch";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!hasValidCronSecret(request, process.env.CRON_SECRET)) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  if (!isKoreanCollectionWeekday(new Date())) {
    return Response.json({ accepted: false, skipped: "WEEKEND" });
  }
  try {
    const settings = readGitHubDispatchSettings();
    if (new URL(request.url).searchParams.has("backup")) {
      await dispatchCollectionWatchdog(settings, "scheduled");
    } else {
      await dispatchCollectorWorkflow(settings, "scheduled", fetch, true);
    }
    return Response.json({ accepted: true }, { status: 202 });
  } catch (error) {
    console.error("daily collector dispatch failed", error);
    return Response.json({ error: "자동 수집 실행 요청에 실패했습니다." }, { status: 500 });
  }
}
