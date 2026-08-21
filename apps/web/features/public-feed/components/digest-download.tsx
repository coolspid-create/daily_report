import type { DigestLink } from "../types/public-feed";

interface DigestDownloadProps {
  digest?: DigestLink;
  topicLabel: string;
}

export function DigestDownload({ digest, topicLabel }: DigestDownloadProps) {
  if (!digest?.available || !digest.url) {
    return null;
  }
  return (
    <a className="digest-link" href={digest.url} target="_blank" rel="noopener noreferrer">
      오늘 정리본 PDF ↓ <span className="sr-only">{topicLabel} (새 창)</span>
    </a>
  );
}
