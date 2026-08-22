import { z } from "zod";

export const deliveryModes = [
  "DIRECT_OFFICIAL_FILE", "OFFICIAL_PAGE_ONLY", "MIRRORED_ALLOWED", "SUMMARY_ONLY", "BLOCKED",
] as const;

export const reviewFormSchema = z.object({
  canonicalTitle: z.string().trim().min(1).max(300),
  institution: z.string().trim().min(1).max(160),
  publishedAt: z.iso.date(),
  primaryTopicId: z.enum(["economy", "industry", "ai-tech", "labor-welfare", "education-population", "land-environment", "law-security"]),
  contentTag: z.string().trim().min(1).max(40),
  whyItMatters: z.string().trim().min(1).max(240),
  keyTags: z.array(z.string().trim().min(1).max(24)).min(1).max(3),
  deliveryMode: z.enum(deliveryModes),
});

export const rejectSchema = z.object({ reason: z.string().trim().min(1).max(300) });
export const batchApproveSchema = z.object({
  documentIds: z.array(z.uuid()).min(1).max(20),
});
export const mergeSchema = z.object({
  targetDocumentId: z.uuid(),
  reason: z.string().trim().min(1).max(300).default("중복 후보 병합"),
});
