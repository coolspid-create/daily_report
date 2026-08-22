"use client";

import { useEffect, useRef, useState } from "react";
import { TOPICS } from "../constants/topics";
import { useFeedSelection } from "../hooks/use-feed-selection";
import { filterFeed } from "../lib/filter-feed";
import type { FeedSelection } from "../lib/initial-selection";
import type { PublicArchive, PublicFeedSnapshot } from "../types/public-feed";
import { ArchiveSelector } from "./archive-selector";
import { FeedHeader } from "./feed-header";
import { FeedSummary } from "./feed-summary";
import { ReportList } from "./report-list";
import { TopicSelector } from "./topic-selector";

interface PublicFeedProps {
  archive: PublicArchive;
  fallbackSnapshot: PublicFeedSnapshot;
  initialSelection: FeedSelection;
}

export function PublicFeed({ archive, fallbackSnapshot, initialSelection }: PublicFeedProps) {
  const mainRef = useRef<HTMLElement>(null);
  const selection = useFeedSelection(initialSelection, archive);
  const [snapshots, setSnapshots] = useState<Record<string, PublicFeedSnapshot>>(
    archive.loadedDate && archive.snapshot ? { [archive.loadedDate]: archive.snapshot } : {},
  );
  const [loadingDate, setLoadingDate] = useState<string | null>(null);
  const snapshot = selection.archiveDate ? snapshots[selection.archiveDate] : archive.snapshot ?? fallbackSnapshot;
  const reports = snapshot ? filterFeed(snapshot, selection.topic) : [];
  const topicLabel = TOPICS.find((topic) => topic.id === selection.topic)?.label ?? "전체";

  useEffect(() => {
    mainRef.current?.setAttribute("data-hydrated", "true");
  }, []);

  useEffect(() => {
    const date = selection.archiveDate;
    if (!date || snapshots[date]) return;
    let cancelled = false;
    setLoadingDate(date);
    void fetch(`/api/public/archive/${date}`)
      .then(async (response) => response.ok ? response.json() as Promise<PublicFeedSnapshot | null> : null)
      .then((nextSnapshot) => {
        if (!cancelled && nextSnapshot) setSnapshots((current) => ({ ...current, [date]: nextSnapshot }));
      })
      .finally(() => { if (!cancelled) setLoadingDate(null); });
    return () => { cancelled = true; };
  }, [selection.archiveDate, snapshots]);

  return (
    <main className="page-shell" ref={mainRef}>
      <FeedHeader generatedAt={snapshot?.generatedAt ?? fallbackSnapshot.generatedAt} />
      <section className="feed-controls" aria-label="피드 선택">
        <TopicSelector activeTopic={selection.topic} onChange={selection.setTopic} />
        <ArchiveSelector activeDate={selection.archiveDate} dates={archive.dates} onChange={selection.setArchiveDate} />
      </section>
      <FeedSummary topic={topicLabel} topicId={selection.topic} count={reports.length} digest={snapshot?.digests[selection.topic]} />
      {loadingDate === selection.archiveDate ? <section className="empty-feed" aria-live="polite"><p>발행본을 불러오는 중입니다.</p></section> : <ReportList reports={reports} topicLabel={topicLabel} />}
      <footer className="site-footer">원문은 각 발행기관의 공식 자료로 연결됩니다.</footer>
    </main>
  );
}
