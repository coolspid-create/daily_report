"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import type { TopicId } from "../constants/topics";
import { buildFeedUrl } from "../lib/build-feed-url";
import type { FeedSelection } from "../lib/initial-selection";
import {
  readStoredTopic,
  storeTopic,
  subscribeToStoredTopic,
} from "../lib/topic-storage";
import type { PublicArchive } from "../types/public-feed";

export function useFeedSelection(initial: FeedSelection, archive: PublicArchive) {
  const topic = useSyncExternalStore(
    subscribeToStoredTopic,
    () =>
      initial.topicFromQuery
        ? initial.topic
        : readStoredTopic(window.localStorage) ?? initial.topic,
    () => initial.topic,
  );
  const [archiveDate, setArchiveDateState] = useState(
    initial.archiveDate && archive.dates.includes(initial.archiveDate)
      ? initial.archiveDate
      : archive.currentDate,
  );

  useEffect(() => {
    window.history.replaceState(null, "", buildFeedUrl(topic, archiveDate, archive.currentDate));
  }, [topic, archiveDate, archive.currentDate]);

  function setTopic(next: TopicId) {
    storeTopic(window.localStorage, next);
  }

  function setArchiveDate(next: string) {
    if (archive.dates.includes(next)) setArchiveDateState(next);
  }

  return { topic, archiveDate, setTopic, setArchiveDate };
}
