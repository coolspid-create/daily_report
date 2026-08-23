interface FeedHeaderProps {
  generatedAt: string;
}

function formatKoreaTimestamp(value: string): string {
  const koreaOffsetMilliseconds = 9 * 60 * 60 * 1000;
  const date = new Date(new Date(value).getTime() + koreaOffsetMilliseconds);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  return `${year}.${month}.${day} ${hour}:${minute} KST`;
}

export function FeedHeader({ generatedAt }: FeedHeaderProps) {
  const updated = formatKoreaTimestamp(generatedAt);

  return (
    <header className="feed-header">
      <div className="feed-header-left">
        <h1>오늘의 공공리포트</h1>
        <p className="subtitle">정부·국회·공공 연구기관의 핵심 보고서를 수집하여 제공합니다.</p>
      </div>
      <div className="feed-header-right">
        <time className="updated-at" dateTime={generatedAt}>
          발행 {updated}
        </time>
      </div>
    </header>
  );
}
