import { createServiceClient } from "@/lib/database/service-client";
import type { SourceContentType, SourceHealth } from "@/features/admin-review/types/admin-review";

function determineReasonCategory(slug: string, status: string, active: boolean, failures: number): string | undefined {
  if (
    slug === "nice-credit-research" ||
    slug === "korea-ratings-research" ||
    slug === "kis-rating-research"
  ) {
    return "스크립트/토큰 (LINK_ONLY)";
  }
  if (slug === "kli-research") {
    return "원천 사이트 점검";
  }
  if (slug === "kihasa-research") {
    return "날짜 정밀도 보완";
  }
  if (
    slug === "kif-financial-brief" ||
    slug === "stepi-research" ||
    slug === "kdi-research"
  ) {
    return "브라우저 렌더링 점검";
  }
  if (failures > 0) {
    return "수집 오류";
  }
  if (!active) {
    return status === "DISABLED" ? "비활성 출처" : "점검 보류";
  }
  return undefined;
}

const CENTRAL_MINISTRY_PRESS_SOURCES: Array<{
  id: string;
  slug: string;
  name: string;
  contentType: SourceContentType;
}> = [
  { id: "moef-press", slug: "moef-press", name: "기획재정부 보도자료", contentType: "PRESS_RELEASE" },
  { id: "fsc-policy", slug: "fsc-policy", name: "금융위원회", contentType: "PRESS_RELEASE" },
  { id: "molit-press", slug: "molit-press", name: "국토교통부 보도자료", contentType: "PRESS_RELEASE" },
  { id: "motie-press", slug: "motie-press", name: "산업통상자원부 보도자료", contentType: "PRESS_RELEASE" },
  { id: "msit-press", slug: "msit-press", name: "과학기술정보통신부 보도자료", contentType: "PRESS_RELEASE" },
  { id: "moel-press", slug: "moel-press", name: "고용노동부 보도자료", contentType: "PRESS_RELEASE" },
  { id: "mof-press", slug: "mof-press", name: "해양수산부 보도자료", contentType: "PRESS_RELEASE" },
  { id: "ftc-press", slug: "ftc-press", name: "공정거래위원회 보도자료", contentType: "PRESS_RELEASE" },
  { id: "mss-press", slug: "mss-press", name: "중소벤처기업부 보도자료", contentType: "PRESS_RELEASE" },
  { id: "mohw-press", slug: "mohw-press", name: "보건복지부 보도자료", contentType: "PRESS_RELEASE" },
];


export async function getSourceHealth(): Promise<SourceHealth[]> {
  const client = createServiceClient();
  const { data, error } = await client
    .from("sources")
    .select("id,slug,name,status,active,last_success_at,last_failure_at,last_error_code,last_error_message,consecutive_failures,consecutive_empty_runs,content_type")
    .order("name");
  if (error) throw new Error("출처 상태를 불러오지 못했습니다.");

  // 최근 실패 실행 기록 조회 (에러 메시지 보완용)
  const { data: latestRuns } = await client
    .from("source_runs")
    .select("source_id,status,error_code,error_message")
    .in("status", ["FAILED", "PARTIAL"])
    .order("finished_at", { ascending: false })
    .limit(50);

  const errorMap = new Map<string, { code?: string; message?: string }>();
  if (latestRuns) {
    for (const run of latestRuns) {
      if (run.source_id && !errorMap.has(run.source_id)) {
        errorMap.set(run.source_id, {
          code: run.error_code ?? undefined,
          message: run.error_message ?? undefined,
        });
      }
    }
  }

  const result: SourceHealth[] = data.map((row) => {
    const errorInfo = errorMap.get(row.id);
    return {
      id: row.id,
      slug: row.slug,
      name: row.name,
      status: row.status,
      active: row.active,
      lastSuccessAt: row.last_success_at,
      lastFailureAt: row.last_failure_at,
      consecutiveFailures: row.consecutive_failures,
      consecutiveEmptyRuns: row.consecutive_empty_runs,
      reasonCategory: determineReasonCategory(
        row.slug,
        row.status,
        row.active,
        row.consecutive_failures
      ),
      lastErrorMessage: row.last_error_message ?? errorInfo?.message ?? null,
      lastErrorCode: row.last_error_code ?? errorInfo?.code ?? null,
      contentType: row.content_type,
    };
  });

  const existingSlugs = new Set(result.map((s) => s.slug));
  for (const item of CENTRAL_MINISTRY_PRESS_SOURCES) {
    if (!existingSlugs.has(item.slug)) {
      result.push({
        id: item.id,
        slug: item.slug,
        name: item.name,
        status: "HEALTHY",
        active: true,
        lastSuccessAt: null,
        consecutiveFailures: 0,
        reasonCategory: "중앙부처 24H 메인 수집",
        lastErrorMessage: null,
        lastErrorCode: null,
        contentType: item.contentType,
      });
    }
  }

  return result.sort((a, b) => a.name.localeCompare(b.name, "ko"));
}
