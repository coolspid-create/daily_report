import type { StoredDocument } from "../types/admin-review";

interface StoredDocumentListProps {
  documents: StoredDocument[];
}

function statusLabel(status: StoredDocument["workflowStatus"]): string {
  if (status === "PUBLISHED") return "발행·보관";
  return status === "APPROVED" ? "승인·보관" : "제외·보관";
}

export function StoredDocumentList({ documents }: StoredDocumentListProps) {
  if (documents.length === 0) {
    return <p className="admin-empty">보관된 문서가 없습니다.</p>;
  }

  return (
    <ul className="stored-document-list" aria-label="보관 문서">
      {documents.map((document) => (
        <li key={document.id}>
          <span className="badge">{statusLabel(document.workflowStatus)}</span>
          <strong>{document.canonicalTitle}</strong>
          <small>{document.institution} · {document.publishedAt}</small>
          <a href={document.primarySourceUrl} target="_blank" rel="noopener noreferrer">공식 출처 ↗</a>
        </li>
      ))}
    </ul>
  );
}
