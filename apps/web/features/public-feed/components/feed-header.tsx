interface FeedHeaderProps {
  generatedAt: string;
}

function formatKoreaTimestamp(value: string): string {
  const koreaOffsetMilliseconds = 9 * 60 * 60 * 1000;
  const date = new Date(new Date(value).getTime() + koreaOffsetMilliseconds);
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  return `${month}. ${day}. ${hour}:${minute}`;
}

export function FeedHeader({ generatedAt }: FeedHeaderProps) {
  const updated = formatKoreaTimestamp(generatedAt);

  return (
    <header className="feed-header">
      <div>
        <p className="eyebrow">TODAY&apos;S PUBLIC REPORTS</p>
        <h1>오늘의 공공리포트</h1>
        <p className="subtitle">
          최근 7일 발행본에서 읽을 만한 공공 리포트만 골랐습니다.
        </p>
      </div>
      <time className="updated-at" dateTime={generatedAt}>
        {updated} 업데이트
      </time>
    </header>
  );
}
