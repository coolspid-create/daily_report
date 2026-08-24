import type { DeliveryMode, SourceContentType } from "@/features/public-feed/types/public-report";

export type { SourceContentType };


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
  createdAt: string;
  sourceContentType: SourceContentType;
  duplicateCandidateIds: string[];
  exceptionReasons: string[];
}

export interface SourceHealth {
  id: string;
  slug?: string;
  name: string;
  status: "HEALTHY" | "DEGRADED" | "DISABLED";
  active: boolean;
  lastSuccessAt: string | null;
  lastFailureAt?: string | null;
  consecutiveFailures: number;
  reasonCategory?: string;
  lastErrorMessage?: string | null;
  lastErrorCode?: string | null;
  contentType: SourceContentType;
}


export interface AutomationStatus {
  id: string;
  status: "RUNNING" | "PUBLISHED" | "PARTIAL" | "FAILED" | "NO_CONTENT" | "DRY_RUN";
  stage: string;
  scheduledFor: string;
  scheduledForLabel: string;
  collectedCount: number;
  reviewCandidateCount: number;
  autoApprovedCount: number;
  exceptionCount: number;
  publishedCount: number;
  errorMessage: string | null;
  telegramDeliveryId: string | null;
  telegramStatus: "PENDING" | "SENDING" | "SENT" | "FAILED" | null;
  telegramError: string | null;
}

export interface PublicationHistory {
  publicationDate: string;
  publishedAt: string | null;
  reportCount: number;
}

export interface StoredDocument {
  id: string;
  canonicalTitle: string;
  institution: string;
  publishedAt: string;
  primarySourceUrl: string;
  workflowStatus: "APPROVED" | "PUBLISHED" | "REJECTED";
  createdAt: string;
  updatedAt: string;
  sourceContentType: SourceContentType;
}
