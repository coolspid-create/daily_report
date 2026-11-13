import Link from "next/link";

interface FeedHeaderProps {
  generatedAt: string;
  onHome: () => void;
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

export function FeedHeader({ generatedAt, onHome }: FeedHeaderProps) {
  const updated = formatKoreaTimestamp(generatedAt);

  return (
    <header className="feed-header">
      <div className="feed-header-left">
        <h1>
          <Link href="/?topic=all" prefetch={false} onClick={(event) => {
            if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            onHome();
          }}>
            오늘의 공공리포트
          </Link>
        </h1>
        <p className="subtitle">정부·국회·공공 연구기관의 핵심 보고서를 수집하여 제공합니다.</p>
      </div>
      <dl className="feed-header-right" aria-label="발행 및 수집 정보">
        <div className="feed-edition-row">
          <dt>발행</dt>
          <dd><time className="updated-at" dateTime={generatedAt}>{updated}</time></dd>
        </div>
        <div className="feed-edition-row">
          <dt>수집 시작</dt>
          <dd className="collection-schedule">리포트 08:35 · 보도자료 10:30 KST</dd>
        </div>
      </dl>
    </header>
  );
}
