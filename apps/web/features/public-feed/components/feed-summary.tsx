import type { DigestLink } from "../types/public-feed";
import { DigestDownload } from "./digest-download";

interface FeedSummaryProps {
  topic: string;
  topicId: string;
  count: number;
  digest?: DigestLink;
}

function description(topicId: string, count: number): string {
  if (topicId === "all") return `최근 7일 꼭 볼 자료 ${count}건`;
  return `최근 7일 선정 자료 ${count}건`;
}

export function FeedSummary({ topic, topicId, count, digest }: FeedSummaryProps) {
  return (
    <section className="feed-summary" aria-live="polite">
      <div>
        <h2>{topic}</h2>
        <p>{description(topicId, count)}</p>
      </div>
      <DigestDownload digest={digest} topicLabel={topic} />
    </section>
  );
}
