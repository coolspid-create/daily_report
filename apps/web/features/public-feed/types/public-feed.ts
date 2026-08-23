import type { PublicReport } from "./public-report";

export type FeedRange = "7d";

export interface TopicSummary {
  id: string;
  label: string;
  count: number;
}

export interface DigestLink {
  available: boolean;
  url?: string | null;
}

export interface PublicFeedSnapshot {
  version: 1;
  generatedAt: string;
  range: FeedRange;
  topics: TopicSummary[];
  reportsByTopic: Record<string, PublicReport[]>;
  digests: Record<string, DigestLink>;
}

export interface PublicArchive {
  currentDate: string | null;
  dates: string[];
  loadedDate: string | null;
  snapshot: PublicFeedSnapshot | null;
}

export interface PublicPressArchive {
  currentDate: string | null;
  dates: string[];
  loadedDate: string | null;
  reports: PublicReport[];
}
