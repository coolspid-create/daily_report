"use client";

import type { SourceHealth } from "@/features/admin-review/types/admin-review";

interface SourceHealthTableProps { sources: SourceHealth[]; onChanged: () => void; }

export function SourceHealthTable({ sources, onChanged }: SourceHealthTableProps) {
  const activeSources = sources.filter((source) => source.active);
  const inactiveSources = sources.filter((source) => !source.active);

  async function toggle(source: SourceHealth) {
    const response = await fetch(`/api/admin/sources/${source.id}/toggle`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ active: !source.active }) });
    if (response.ok) onChanged();
  }
  return (
    <section className="source-table" aria-label="출처 상태">
      <div className="active-sources-heading">
        <span>활성 출처 {activeSources.length}곳</span>
      </div>
      <div role="table" aria-label="활성 출처 상태">

      {activeSources.map((source) => (
        <div className="source-row" role="row" key={source.id}>
          <div className="source-name-cell">
            <strong>{source.name}</strong>
            {source.reasonCategory ? <span className="reason-tag">{source.reasonCategory}</span> : null}
            {source.lastErrorMessage ? (
              <span className="source-error-hint" title={`최근 오류: ${source.lastErrorMessage}`}>
                ⚠ {source.lastErrorMessage}
              </span>
            ) : null}
          </div>
          <span className="badge">{source.status}</span>
          <span>연속 실패 {source.consecutiveFailures}회</span>
          {source.consecutiveEmptyRuns ? <span>연속 빈 수집 {source.consecutiveEmptyRuns}회</span> : null}
          <span>{source.lastSuccessAt ?? "성공 기록 없음"}</span>
          <button type="button" onClick={() => toggle(source)}>{source.active ? "비활성화" : "활성화"}</button>
        </div>
      ))}
      </div>
      {inactiveSources.length > 0 ? (
        <details className="inactive-sources">
          <summary>비활성 출처 {inactiveSources.length}곳 보기</summary>
          <div role="table" aria-label="비활성 출처 상태">
            {inactiveSources.map((source) => (
              <div className="source-row" role="row" key={source.id}>
                <div className="source-name-cell">
                  <strong>{source.name}</strong>
                  {source.reasonCategory ? <span className="reason-tag">{source.reasonCategory}</span> : null}
                  {source.lastErrorMessage ? (
                    <span className="source-error-hint" title={`최근 오류: ${source.lastErrorMessage}`}>
                      ⚠ {source.lastErrorMessage}
                    </span>
                  ) : null}
                </div>
                <span className="badge">{source.status}</span>
                <span>연속 실패 {source.consecutiveFailures}회</span>
                {source.consecutiveEmptyRuns ? <span>연속 빈 수집 {source.consecutiveEmptyRuns}회</span> : null}
                <span>{source.lastSuccessAt ?? "성공 기록 없음"}</span>
                <button type="button" onClick={() => toggle(source)}>활성화</button>
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </section>
  );

}
