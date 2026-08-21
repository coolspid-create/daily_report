import { TOPIC_IDS, type TopicId } from "../constants/topics";

export interface FeedSelection {
  topic: TopicId;
  archiveDate: string | null;
  topicFromQuery: boolean;
}

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export function parseInitialSelection(
  query: Record<string, string | string[] | undefined>,
): FeedSelection {
  const topic = first(query.topic);
  const archiveDate = first(query.date);
  return {
    topic: topic && TOPIC_IDS.has(topic as TopicId) ? (topic as TopicId) : "all",
    archiveDate: archiveDate && /^\\d{4}-\\d{2}-\\d{2}$/.test(archiveDate) ? archiveDate : null,
    topicFromQuery: Boolean(topic && TOPIC_IDS.has(topic as TopicId)),
  };
}
