import type { TopicId } from "../constants/topics";
import type { PublicFeedSnapshot } from "../types/public-feed";
import type { PublicReport } from "../types/public-report";

export function filterFeed(snapshot: PublicFeedSnapshot, topic: TopicId): PublicReport[] {
  return snapshot.reportsByTopic[topic] ?? [];
}
