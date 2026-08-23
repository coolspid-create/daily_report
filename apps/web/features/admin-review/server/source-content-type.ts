import type { SourceContentType } from "@/features/public-feed/types/public-report";

interface DocumentSourceRow {
  sources: { content_type: SourceContentType | null }[] | null;
}

export function resolveSourceContentType(sources: DocumentSourceRow[] | null | undefined): SourceContentType {
  return sources
    ?.flatMap((source) => source.sources ?? [])
    .find((source) => source.content_type)?.content_type ?? "REPORT";
}
