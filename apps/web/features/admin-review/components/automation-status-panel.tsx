"use client";

import { useRouter } from "next/navigation";
import type { AutomationStatus } from "../types/admin-review";

export function AutomationStatusPanel({ status }: { status: AutomationStatus | null }) {
  const router = useRouter();
  const retry = async () => {
    if (!status?.telegramDeliveryId) return;
    const response = await fetch(`/api/admin/telegram/${status.telegramDeliveryId}/retry`, { method: "POST" });
    if (response.ok) router.refresh();
  };
  if (!status) return <section className="automation-status"><strong>자동 발행 이력 없음</strong><p>첫 예약 실행 후 상태가 표시됩니다.</p></section>;
  return (
    <section className="automation-status" aria-label="최근 자동 발행 상태">
      <div><strong>최근 자동 발행 · {status.status}</strong><small>{status.scheduledForLabel}</small></div>
      <dl><div><dt>수집 후보</dt><dd>{status.collectedCount}</dd></div><div><dt>자동 승인</dt><dd>{status.autoApprovedCount}</dd></div><div><dt>예외</dt><dd>{status.exceptionCount}</dd></div><div><dt>발행</dt><dd>{status.publishedCount}</dd></div></dl>
      <p>단계 {status.stage} · Telegram {status.telegramStatus ?? "비활성"}</p>
      {(status.errorMessage || status.telegramError) && <p className="form-error">{status.errorMessage ?? status.telegramError}</p>}
      {status.telegramStatus === "FAILED" && <button type="button" onClick={retry}>Telegram 재시도 예약</button>}
    </section>
  );
}
