"use client";

import { useEffect, useState } from "react";
import type { TopicId } from "../constants/topics";
import { buildFeedUrl } from "../lib/build-feed-url";
import type { FeedSelection } from "../lib/initial-selection";
import { readStoredTopic, storeTopic } from "../lib/topic-storage";
import type { PublicArchive, PublicPressArchive } from "../types/public-feed";

export function useFeedSelection(
  initial: FeedSelection,
  archive: PublicArchive,
  pressArchive: PublicPressArchive,
) {
  const [topic, setTopicState] = useState<TopicId>(() => {
    if (initial.topicFromQuery) return initial.topic;
    if (typeof window !== "undefined") {
      const stored = readStoredTopic(window.localStorage);
      if (stored) return stored;
    }
    return initial.topic;
  });

  const [archiveDate, setArchiveDateState] = useState(
    initial.archiveDate && archive.dates.includes(initial.archiveDate)
      ? initial.archiveDate
      : archive.currentDate,
  );
  const [pressArchiveDate, setPressArchiveDateState] = useState(
    initial.pressArchiveDate && pressArchive.dates.includes(initial.pressArchiveDate)
      ? initial.pressArchiveDate
      : pressArchive.currentDate,
  );

  useEffect(() => {
    window.history.replaceState(
      null,
      "",
      buildFeedUrl(topic, archiveDate, archive.currentDate, pressArchiveDate, pressArchive.currentDate),
    );
  }, [topic, archiveDate, archive.currentDate, pressArchiveDate, pressArchive.currentDate]);

  function setTopic(next: TopicId) {
    setTopicState(next);
    if (typeof window !== "undefined") {
      storeTopic(window.localStorage, next);
    }
  }

  function setArchiveDate(next: string) {
    if (archive.dates.includes(next)) setArchiveDateState(next);
  }

  function setPressArchiveDate(next: string) {
    if (pressArchive.dates.includes(next)) setPressArchiveDateState(next);
  }

  return { topic, archiveDate, pressArchiveDate, setTopic, setArchiveDate, setPressArchiveDate };
}
