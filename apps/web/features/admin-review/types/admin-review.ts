import type { DeliveryMode } from "@/features/public-feed/types/public-report";

export interface ReviewItem {
  id: string;
  canonicalTitle: string;
  institution: string;
  publishedAt: string;
  primaryTopicId: string;
  contentTag: string;
  whyItMatters: string;
  keyTags: string[];
  deliveryMode: DeliveryMode;
  workflowStatus: "NEW" | "NEEDS_REVIEW" | "APPROVED" | "REJECTED" | "PUBLISHED";
  primarySourceUrl: string;
  duplicateCandidateIds: string[];
  exceptionReasons: string[];
}

export interface SourceHealth {
  id: string;
  name: string;
  status: "HEALTHY" | "DEGRADED" | "DISABLED";
  active: boolean;
  lastSuccessAt: string | null;
  consecutiveFailures: number;
}

export interface AutomationStatus {
  id: string;
  status: "RUNNING" | "PUBLISHED" | "PARTIAL" | "FAILED" | "NO_CONTENT" | "DRY_RUN";
  stage: string;
  scheduledFor: string;
  scheduledForLabel: string;
  collectedCount: number;
  autoApprovedCount: number;
  exceptionCount: number;
  publishedCount: number;
  errorMessage: string | null;
  telegramDeliveryId: string | null;
  telegramStatus: "PENDING" | "SENDING" | "SENT" | "FAILED" | null;
  telegramError: string | null;
}
