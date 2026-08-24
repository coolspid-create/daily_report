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
import { isBulkApprovalEligible } from "../lib/review-eligibility";

interface ReviewWorkbenchProps {
  items: ReviewItem[];
  sources: SourceHealth[];
  automation: AutomationStatus | null;
  publications: PublicationHistory[];
  storedDocuments: StoredDocument[];
  eligibilityNow: string;
}

const isPressItem = (item: ReviewItem) => item.sourceContentType === "PRESS_RELEASE";

const isPressSource = (source: SourceHealth) => source.contentType === "PRESS_RELEASE";

const isPressStored = (doc: StoredDocument) => doc.sourceContentType === "PRESS_RELEASE";

export function ReviewWorkbench({
  items,
  sources,
  automation,
  publications,
  storedDocuments,
  eligibilityNow,
}: ReviewWorkbenchProps) {
  const router = useRouter();
  const [adminMode, setAdminMode] = useState<"reports" | "press">("reports");
  const [view, setView] = useState<"review" | "published" | "stored" | "sources">("review");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const eligibilityReference = new Date(eligibilityNow);

  const pressItems = items.filter(isPressItem);
  const visibleItems = adminMode === "press" ? pressItems : items.filter((item) => !isPressItem(item));
  const visibleSources = sources.filter((s) => (adminMode === "press" ? isPressSource(s) : !isPressSource(s)));
  const visibleStored = storedDocuments.filter((d) => (adminMode === "press" ? isPressStored(d) : !isPressStored(d)));

  const selectedId = visibleItems.some((item) => item.id === activeId) ? activeId : (visibleItems[0]?.id ?? null);
  const active = visibleItems.find((item) => item.id === selectedId) ?? null;

  const recentIds = visibleItems
    .filter(
      (item) =>
        item.workflowStatus === "NEEDS_REVIEW" &&
        isBulkApprovalEligible(item.sourceContentType, item.createdAt, item.publishedAt, eligibilityReference),
    )
    .slice(0, 20)
    .map((item) => item.id);

  const handleModeChange = (mode: "reports" | "press") => {
    setAdminMode(mode);
    setActiveId(null);
    if (mode === "press" && view === "published") {
      setView("review");
    }
  };

  const approveLatest = async () => {
    const label = adminMode === "press" ? "최근 24시간 발행본" : "최근 7일 발행본";
    if (recentIds.length === 0 || !window.confirm(`${label} 중 발행일이 확인된 ${recentIds.length}건을 한 번에 승인하시겠습니까?`)) return;
    setMessage(null);
    const response = await fetch("/api/admin/documents/batch-approve", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ documentIds: recentIds }),
    });
    const result = (await response.json()) as {
      count?: number;
      error?: string;
      refresh?: { status: string; message?: string };
    };
    if (!response.ok) {
      setMessage(result.error ?? "일괄 승인에 실패했습니다.");
      return;
    }
    setMessage(
      result.refresh?.status === "QUEUED"
        ? `${result.count ?? 0}건을 승인했고 공개 피드 재발행을 요청했습니다.`
        : `${result.count ?? 0}건을 승인했습니다. ${result.refresh?.message ?? "재발행 요청은 다시 시도해 주세요."}`
    );
    router.refresh();
  };

  const activeSourcesCount = visibleSources.filter((s) => s.active).length;
  const inactiveSourcesCount = visibleSources.length - activeSourcesCount;

  return (
    <main className="admin-shell">
      <header className="admin-header">
        <div>
          <p className="eyebrow">ADMIN WORKBENCH</p>
          <h1>발행 관리</h1>
          <p>공공리포트와 보도자료를 분리하여 검수하고 수집 출처를 관리합니다.</p>
        </div>
        <nav aria-label="관리자 보기">
          <button aria-pressed={view === "review"} onClick={() => setView("review")}>
            {adminMode === "press" ? "보도자료 검수" : "검수 대기"} {visibleItems.length}
          </button>
          {adminMode === "reports" && (
            <button aria-pressed={view === "published"} onClick={() => setView("published")}>
              발행 이력 {publications.length}
            </button>
          )}
          <button aria-pressed={view === "stored"} onClick={() => setView("stored")}>
            보관함 {visibleStored.length}
          </button>
          <button aria-pressed={view === "sources"} onClick={() => setView("sources")}>
            출처 상태 {activeSourcesCount}
          </button>
        </nav>
      </header>

      <div className="admin-mode-tabs" role="tablist" aria-label="관리 영역 선택">
        <button
          type="button"
          className={`admin-mode-tab ${adminMode === "reports" ? "is-active" : ""}`}
          onClick={() => handleModeChange("reports")}
          aria-pressed={adminMode === "reports"}
        >
          📑 공공리포트 관리 ({items.filter((i) => !isPressItem(i)).length})
        </button>
        <button
          type="button"
          className={`admin-mode-tab ${adminMode === "press" ? "is-active" : ""}`}
          onClick={() => handleModeChange("press")}
          aria-pressed={adminMode === "press"}
        >
          📰 보도자료 관리 ({pressItems.length})
        </button>
      </div>

      {message && (
        <p className="form-message" role="status">
          {message}
        </p>
      )}

      {view === "review" && adminMode === "reports" && <AutomationStatusPanel status={automation} />}

      {view === "review" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h2>{adminMode === "press" ? "보도자료 검수 대기" : "공공리포트 검수 대기"}</h2>
              <p>
                {adminMode === "press"
                  ? "수집된 24시간 정부·공공기관 보도자료를 검토하고 승인합니다."
                  : "자동 발행에서 제외된 자료입니다. 내용을 확인한 뒤 승인하거나 제외해 주세요."}
              </p>
            </div>
            <button type="button" disabled={recentIds.length === 0} onClick={approveLatest}>
              발행 가능 {recentIds.length}건 일괄 승인
            </button>
          </div>
          <div className="workbench">
            <ReviewList items={visibleItems} activeId={selectedId} onSelect={setActiveId} />
            {active ? (
              <ReviewEditor key={active.id} item={active} onChanged={() => router.refresh()} />
            ) : (
              <p className="admin-empty">검수할 문서가 없습니다.</p>
            )}
          </div>
        </section>
      )}

      {view === "published" && adminMode === "reports" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h2>발행 이력</h2>
              <p>날짜별 공개 피드를 확인할 수 있습니다.</p>
            </div>
          </div>
          <PublicationHistoryList publications={publications} />
        </section>
      )}

      {view === "stored" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h2>{adminMode === "press" ? "보도자료 보관함" : "공공리포트 보관함"}</h2>
              <p>승인 또는 제외 처리한 자료를 최근 처리 순서로 확인합니다.</p>
            </div>
          </div>
          <StoredDocumentList documents={visibleStored} />
        </section>
      )}

      {view === "sources" && (
        <section className="admin-section">
          <div className="admin-section-heading">
            <div>
              <h2>{adminMode === "press" ? "보도자료 수집 출처" : "공공리포트 수집 출처"}</h2>
              <p>
                수집 출처를 활성화하거나 상태를 확인합니다. (활성 {activeSourcesCount}곳 / 비활성 {inactiveSourcesCount}곳, 총 {visibleSources.length}곳)
              </p>
            </div>
          </div>
          <SourceHealthTable sources={visibleSources} onChanged={() => router.refresh()} />
        </section>
      )}
    </main>
  );
}
