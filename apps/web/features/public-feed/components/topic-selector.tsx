import { RESEARCH_TOPICS, type TopicId } from "../constants/topics";
import type { TopicSummary } from "../types/public-feed";

interface TopicSelectorProps {
  activeTopic: TopicId;
  topicSummaries?: TopicSummary[];
  onChange: (topic: TopicId) => void;
}

export function TopicSelector({
  activeTopic,
  topicSummaries,
  onChange,
}: TopicSelectorProps) {
  const countMap = new Map((topicSummaries ?? []).map((t) => [t.id, t.count]));

  return (
    <div className="topic-scroll" role="group" aria-label="공공리포트 분류">
      {RESEARCH_TOPICS.map((topic) => {
        const count = countMap.get(topic.id);
        return (
          <button
            className="pill"
            key={topic.id}
            type="button"
            aria-label={topic.label}
            aria-pressed={activeTopic === topic.id}
            onClick={() => onChange(topic.id)}
          >
            <span>{topic.label}</span>
            {count !== undefined && count > 0 && (
              <span className="topic-count" aria-hidden="true">
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
