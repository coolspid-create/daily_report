import { createServiceClient } from "@/lib/database/service-client";
import type { SourceHealth } from "@/features/admin-review/types/admin-review";

function determineReasonCategory(slug: string, status: string, active: boolean, failures: number): string | undefined {
  if (slug === "mof-press" || slug === "fsc-policy") {
    return "정책 보류 (보도자료 제외)";
  }
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

export async function getSourceHealth(): Promise<SourceHealth[]> {
  const client = createServiceClient();
  const { data, error } = await client
    .from("sources")
    .select("id,slug,name,status,active,last_success_at,consecutive_failures")
    .order("name");
  if (error) throw new Error("출처 상태를 불러오지 못했습니다.");

  // 최근 실패 실행 기록 조회 (에러 메시지 매핑용)
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

  return data.map((row) => {
    const errorInfo = errorMap.get(row.id);
    return {
      id: row.id,
      slug: row.slug,
      name: row.name,
      status: row.status,
      active: row.active,
      lastSuccessAt: row.last_success_at,
      consecutiveFailures: row.consecutive_failures,
      reasonCategory: determineReasonCategory(
        row.slug,
        row.status,
        row.active,
        row.consecutive_failures
      ),
      lastErrorMessage: errorInfo?.message ?? null,
      lastErrorCode: errorInfo?.code ?? null,
    };
  }) as SourceHealth[];
}

