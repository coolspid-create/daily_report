"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { AutomationStatus, PublicationHistory, ReviewItem, SourceHealth, StoredDocument } from "../types/admin-review";
import { AutomationStatusPanel } from "./automation-status-panel";
import { PublicationHistory as PublicationHistoryList } from "./publication-history";
import { ReviewEditor } from "./review-editor";
import { ReviewList } from "./review-list";
import { StoredDocumentList } from "./stored-document-list";
import { SourceHealthTable } from "@/features/source-health/components/source-health-table";

interface ReviewWorkbenchProps {
  items: ReviewItem[];
  sources: SourceHealth[];
  automation: AutomationStatus | null;
  publications: PublicationHistory[];
  storedDocuments: StoredDocument[];
}

export function ReviewWorkbench({ items, sources, automation, publications, storedDocuments }: ReviewWorkbenchProps) {
  const router = useRouter();
  const [view, setView] = useState<"review" | "published" | "stored" | "sources">("review");
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
      <header className="admin-header">
        <div><p className="eyebrow">ADMIN</p><h1>발행 관리</h1><p>수집 자료를 확인하고, 발행 이력과 보관 문서를 관리합니다.</p></div>
        <nav aria-label="관리자 보기">
          <button aria-pressed={view === "review"} onClick={() => setView("review")}>검수 대기 {items.length}</button>
          <button aria-pressed={view === "published"} onClick={() => setView("published")}>발행 이력 {publications.length}</button>
          <button aria-pressed={view === "stored"} onClick={() => setView("stored")}>보관함 {storedDocuments.length}</button>
          <button aria-pressed={view === "sources"} onClick={() => setView("sources")}>출처 상태</button>
        </nav>
      </header>
      {message && <p className="form-message" role="status">{message}</p>}
      {view === "review" && <AutomationStatusPanel status={automation} />}
      {view === "review" && (
        <section className="admin-section">
          <div className="admin-section-heading"><div><h2>검수 대기</h2><p>자동 발행에서 제외된 자료입니다. 내용을 확인한 뒤 승인하거나 제외해 주세요.</p></div><button type="button" disabled={recentIds.length === 0} onClick={approveLatest}>최근 7일 {recentIds.length}건 일괄 승인</button></div>
          <div className="workbench"><ReviewList items={items} activeId={activeId} onSelect={setActiveId} />{active ? <ReviewEditor key={active.id} item={active} onChanged={() => router.refresh()} /> : <p className="admin-empty">검수할 문서가 없습니다.</p>}</div>
        </section>
      )}
      {view === "published" && <section className="admin-section"><div className="admin-section-heading"><div><h2>발행 이력</h2><p>날짜별 공개 피드를 확인할 수 있습니다.</p></div></div><PublicationHistoryList publications={publications} /></section>}
      {view === "stored" && <section className="admin-section"><div className="admin-section-heading"><div><h2>보관함</h2><p>승인 또는 제외 처리한 자료를 최근 처리 순서로 확인합니다.</p></div></div><StoredDocumentList documents={storedDocuments} /></section>}
      {view === "sources" && <section className="admin-section"><div className="admin-section-heading"><div><h2>출처 상태</h2><p>수집 출처를 활성화하거나 상태를 확인합니다.</p></div></div><SourceHealthTable sources={sources} onChanged={() => router.refresh()} /></section>}
    </main>
  );
}
