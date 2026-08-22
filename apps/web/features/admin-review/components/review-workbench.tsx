"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { AutomationStatus, ReviewItem, SourceHealth } from "../types/admin-review";
import { AutomationStatusPanel } from "./automation-status-panel";
import { ReviewEditor } from "./review-editor";
import { ReviewList } from "./review-list";
import { SourceHealthTable } from "@/features/source-health/components/source-health-table";

interface ReviewWorkbenchProps { items: ReviewItem[]; sources: SourceHealth[]; automation: AutomationStatus | null; }

export function ReviewWorkbench({ items, sources, automation }: ReviewWorkbenchProps) {
  const router = useRouter();
  const [view, setView] = useState<"review" | "sources">("review");
  const [activeId, setActiveId] = useState(items[0]?.id ?? null);
  const [message, setMessage] = useState<string | null>(null);
  const active = items.find((item) => item.id === activeId) ?? null;
  const recentIds = items
    .filter((item) => item.workflowStatus === "NEEDS_REVIEW")
    .slice(0, 20)
    .map((item) => item.id);
  const approveLatest = async () => {
    if (recentIds.length === 0 || !window.confirm(`최근 7일 자료 ${recentIds.length}건을 한 번에 승인하시겠습니까?`)) return;
    setMessage(null);
    const response = await fetch("/api/admin/documents/batch-approve", {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ documentIds: recentIds }),
    });
    const result = await response.json() as { count?: number; error?: string; refresh?: { status: string; message?: string } };
    if (!response.ok) {
      setMessage(result.error ?? "일괄 승인에 실패했습니다.");
      return;
    }
    setMessage(result.refresh?.status === "QUEUED"
      ? `${result.count ?? 0}건을 승인했고 공개 피드 재발행을 요청했습니다.`
      : `${result.count ?? 0}건을 승인했습니다. ${result.refresh?.message ?? "재발행 요청은 다시 시도해 주세요."}`);
    router.refresh();
  };
  return (
    <main className="admin-shell">
      <header className="admin-header"><div><p className="eyebrow">ADMIN</p><h1>예외 검수</h1></div><nav aria-label="관리자 보기"><button aria-pressed={view === "review"} onClick={() => setView("review")}>예외 {items.length}</button><button type="button" disabled={recentIds.length === 0} onClick={approveLatest}>최근 7일 {recentIds.length}건 승인</button><button aria-pressed={view === "sources"} onClick={() => setView("sources")}>출처 상태</button></nav></header>
      {message && <p className="form-message" role="status">{message}</p>}
      <AutomationStatusPanel status={automation} />
      {view === "sources" ? <SourceHealthTable sources={sources} onChanged={() => router.refresh()} /> : (
        <div className="workbench"><ReviewList items={items} activeId={activeId} onSelect={setActiveId} />{active ? <ReviewEditor key={active.id} item={active} onChanged={() => router.refresh()} /> : <p>검수할 문서가 없습니다.</p>}</div>
      )}
    </main>
  );
}
