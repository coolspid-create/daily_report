import type { PublicationHistory as PublicationHistoryEntry } from "../types/admin-review";

interface PublicationHistoryProps {
  publications: PublicationHistoryEntry[];
}

function formatDate(value: string): string {
  return value.replaceAll("-", ".");
}

export function PublicationHistory({ publications }: PublicationHistoryProps) {
  if (publications.length === 0) {
    return <p className="admin-empty">아직 발행한 일일 리포트가 없습니다.</p>;
  }

  return (
    <ul className="admin-history-list" aria-label="발행 이력">
      {publications.map((publication) => (
        <li key={publication.publicationDate}>
          <div>
            <strong>{formatDate(publication.publicationDate)} 발행본</strong>
            <small>선정 자료 {publication.reportCount}건</small>
          </div>
          <a href={`/?date=${publication.publicationDate}`}>공개 피드 보기</a>
        </li>
      ))}
    </ul>
  );
}
