interface EmptyFeedProps {
  topicLabel: string;
}

export function EmptyFeed({ topicLabel }: EmptyFeedProps) {
  return (
    <section className="empty-feed" aria-live="polite">
      <p>최근 7일 발행본에 ${topicLabel} 자료가 없습니다.</p>
    </section>
  );
}
