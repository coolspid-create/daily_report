"use client";

import { useState, type FormEvent } from "react";
import { TOPICS } from "@/features/public-feed/constants/topics";
import type { ReviewItem } from "../types/admin-review";
import { deliveryModes } from "../schemas/review-form.schema";

interface ReviewEditorProps { item: ReviewItem; onChanged: () => void; }

async function send(url: string, body: unknown) {
  const response = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) throw new Error("작업을 완료하지 못했습니다.");
}

export function ReviewEditor({ item, onChanged }: ReviewEditorProps) {
  const [message, setMessage] = useState<string | null>(null);
  const [mergeTarget, setMergeTarget] = useState("");

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      canonicalTitle: form.get("canonicalTitle"), institution: form.get("institution"),
      publishedAt: form.get("publishedAt"), primaryTopicId: form.get("primaryTopicId"),
      contentTag: form.get("contentTag"), whyItMatters: form.get("whyItMatters"),
      keyTags: [form.get("keyTag1"), form.get("keyTag2"), form.get("keyTag3")].filter(Boolean),
      deliveryMode: form.get("deliveryMode"),
    };
    try { await send(`/api/admin/documents/${item.id}/update`, payload); setMessage("저장했습니다."); onChanged(); }
    catch { setMessage("저장하지 못했습니다."); }
  }

  async function decide(action: "approve" | "reject") {
    const body = action === "reject" ? { reason: "관리자 검수 제외" } : {};
    try { await send(`/api/admin/documents/${item.id}/${action}`, body); setMessage(action === "approve" ? "승인했습니다." : "제외했습니다."); onChanged(); }
    catch { setMessage("상태를 변경하지 못했습니다."); }
  }

  async function mergeDuplicate() {
    try {
      await send(`/api/admin/documents/${item.id}/merge`, {
        targetDocumentId: mergeTarget,
        reason: "관리자 중복 후보 병합",
      });
      setMessage("중복 문서를 병합했습니다.");
      onChanged();
    } catch {
      setMessage("중복 문서를 병합하지 못했습니다.");
    }
  }

  return (
    <form className="review-editor" onSubmit={save}>
      <a href={item.primarySourceUrl} target="_blank" rel="noopener noreferrer">공식 출처 열기 (새 창)</a>
      <label>제목<input name="canonicalTitle" defaultValue={item.canonicalTitle} required /></label>
      <label>기관<input name="institution" defaultValue={item.institution} required /></label>
      <label>발행일<input name="publishedAt" type="date" defaultValue={item.publishedAt} required /></label>
      <label>대표 분야<select name="primaryTopicId" defaultValue={item.primaryTopicId}>{TOPICS.filter((topic) => topic.id !== "all").map((topic) => <option key={topic.id} value={topic.id}>{topic.label}</option>)}</select></label>
      <label>콘텐츠 태그<input name="contentTag" defaultValue={item.contentTag} required /></label>
      <label>왜 볼 만한가<textarea name="whyItMatters" defaultValue={item.whyItMatters} required /></label>
      {[0, 1, 2].map((index) => <label key={index}>핵심 키워드 {index + 1}<input name={`keyTag${index + 1}`} defaultValue={item.keyTags[index] ?? ""} required={index === 0} /></label>)}
      <label>전달 모드<select name="deliveryMode" defaultValue={item.deliveryMode}>{deliveryModes.map((mode) => <option key={mode}>{mode}</option>)}</select></label>
      <fieldset className="merge-controls">
        <legend>중복 후보 병합</legend>
        {item.duplicateCandidateIds.length > 0 && (
          <p>
            해시 일치 후보: {item.duplicateCandidateIds.map((id) => (
              <button key={id} type="button" onClick={() => setMergeTarget(id)}>
                {id}
              </button>
            ))}
          </p>
        )}
        <label>
          유지할 문서 ID
          <input
            value={mergeTarget}
            onChange={(event) => setMergeTarget(event.target.value)}
            placeholder="UUID"
          />
        </label>
        <button type="button" disabled={!mergeTarget} onClick={mergeDuplicate}>
          이 문서를 대상에 병합
        </button>
      </fieldset>
      {message && <p aria-live="polite">{message}</p>}
      <div className="review-buttons"><button type="button" onClick={() => decide("reject")}>제외</button><button type="submit">보류·저장</button><button type="button" onClick={() => decide("approve")}>승인</button></div>
    </form>
  );
}
