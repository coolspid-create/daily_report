"use client";

import { useEffect, useRef } from "react";
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
  const snapshot = selection.archiveDate
    ? archive.snapshotsByDate[selection.archiveDate] ?? fallbackSnapshot
    : fallbackSnapshot;
  const reports = filterFeed(snapshot, selection.topic);
  const topicLabel = TOPICS.find((topic) => topic.id === selection.topic)?.label ?? "전체";

  useEffect(() => {
    mainRef.current?.setAttribute("data-hydrated", "true");
  }, []);

  return (
    <main className="page-shell" ref={mainRef}>
      <FeedHeader generatedAt={snapshot.generatedAt} />
      <section className="feed-controls" aria-label="피드 선택">
        <TopicSelector activeTopic={selection.topic} onChange={selection.setTopic} />
        <ArchiveSelector activeDate={selection.archiveDate} dates={archive.dates} onChange={selection.setArchiveDate} />
      </section>
      <FeedSummary topic={topicLabel} topicId={selection.topic} count={reports.length} digest={snapshot.digests[selection.topic]} />
      <ReportList reports={reports} topicLabel={topicLabel} />
      <footer className="site-footer">원문은 각 발행기관의 공식 자료로 연결됩니다.</footer>
    </main>
  );
}
