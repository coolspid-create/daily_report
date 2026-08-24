import type { SourceContentType } from "@/features/public-feed/types/public-report";

interface SourceItem {
  content_type?: SourceContentType | null;
}

interface DocumentSourceRow {
  sources?: SourceItem | SourceItem[] | null;
}

export function resolveSourceContentType(
  sources: DocumentSourceRow[] | unknown,
  contentTag?: string | null,
  institution?: string | null,
): SourceContentType {
  const explicitTypes: SourceContentType[] = [];
  if (Array.isArray(sources)) {
    for (const item of sources) {
      const src = (item as DocumentSourceRow)?.sources;
      if (Array.isArray(src)) {
        for (const s of src) {
          if (s?.content_type) explicitTypes.push(s.content_type);
        }
      } else if (src && typeof src === "object" && "content_type" in src) {
        const contentType = (src as SourceItem).content_type;
        if (contentType) explicitTypes.push(contentType);
      }
    }
  }
  if (explicitTypes.includes("PRESS_RELEASE")) return "PRESS_RELEASE";
  if (explicitTypes.includes("REPORT")) return "REPORT";
  if (contentTag === "보도자료" || institution?.includes("보도자료")) {
    return "PRESS_RELEASE";
  }
  return "REPORT";
}
