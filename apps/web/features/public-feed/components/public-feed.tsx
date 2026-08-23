"use client";

import { useEffect, useRef, useState } from "react";
import { TOPICS } from "../constants/topics";
import { useFeedSelection } from "../hooks/use-feed-selection";
import { filterFeed } from "../lib/filter-feed";
import type { FeedSelection } from "../lib/initial-selection";
import type { PublicArchive, PublicFeedSnapshot } from "../types/public-feed";
import { ArchiveSelector } from "./archive-selector";
import { FeedHeader } from "./feed-header";
import { FeedSummary, type ViewMode } from "./feed-summary";
import { PressReleaseSection } from "./press-release-section";
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
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [snapshots, setSnapshots] = useState<Record<string, PublicFeedSnapshot>>(
    archive.loadedDate && archive.snapshot ? { [archive.loadedDate]: archive.snapshot } : {},
  );
  const [loadingDate, setLoadingDate] = useState<string | null>(null);

  const snapshot = selection.archiveDate
    ? snapshots[selection.archiveDate] ??
      (selection.archiveDate === archive.loadedDate ? archive.snapshot : null) ??
      fallbackSnapshot
    : archive.snapshot ?? fallbackSnapshot;

  const allReports = snapshot ? (snapshot.reportsByTopic["all"] ?? []) : [];
  const allPressReleases = allReports.filter(
    (r) => r.contentTag === "보도자료" || r.institution.includes("보도자료")
  );

  const isPressReleaseTab = selection.topic === "press-release";
  const topicReports = snapshot ? filterFeed(snapshot, selection.topic) : [];
  const researchReports = topicReports.filter(
    (r) => r.contentTag !== "보도자료" && !r.institution.includes("보도자료")
  );

  const topicLabel = TOPICS.find((topic) => topic.id === selection.topic)?.label ?? "전체";
  const displayCount = isPressReleaseTab ? allPressReleases.length : researchReports.length;

  useEffect(() => {
    mainRef.current?.setAttribute("data-hydrated", "true");
  }, []);

  const handleArchiveDateChange = (date: string) => {
    selection.setArchiveDate(date);
    if (!snapshots[date] && !(date === archive.loadedDate && archive.snapshot)) {
      setLoadingDate(date);
      void fetch(`/api/public/archive/${date}`)
        .then(async (response) => (response.ok ? (response.json() as Promise<PublicFeedSnapshot | null>) : null))
        .then((nextSnapshot) => {
          if (nextSnapshot) {
            setSnapshots((current) => ({ ...current, [date]: nextSnapshot }));
          }
        })
        .finally(() => {
          setLoadingDate(null);
        });
    }
  };

  return (
    <main className="page-shell" ref={mainRef}>
      <FeedHeader generatedAt={snapshot?.generatedAt ?? fallbackSnapshot.generatedAt} />
      <section className="feed-controls" aria-label="피드 선택">
        <TopicSelector
          activeTopic={selection.topic}
          topicSummaries={snapshot?.topics}
          pressReleaseCount={allPressReleases.length}
          onChange={selection.setTopic}
        />
        <ArchiveSelector
          activeDate={selection.archiveDate}
          dates={archive.dates}
          onChange={handleArchiveDateChange}
        />
      </section>
      <FeedSummary
        topic={topicLabel}
        topicId={selection.topic}
        count={displayCount}
        digest={isPressReleaseTab ? undefined : snapshot?.digests[selection.topic]}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />
      {loadingDate === selection.archiveDate ? (
        <section className="empty-feed" aria-live="polite">
          <p>발행본을 불러오는 중입니다.</p>
        </section>
      ) : isPressReleaseTab ? (
        <PressReleaseSection reports={allPressReleases} />
      ) : (
        <ReportList reports={researchReports} topicLabel={topicLabel} viewMode={viewMode} />
      )}
      <footer className="site-footer">원문 및 PDF 저작권은 각 발행기관의 공식 정책을 따릅니다.</footer>
    </main>
  );
}


