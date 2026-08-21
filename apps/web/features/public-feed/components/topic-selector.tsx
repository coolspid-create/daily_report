import { TOPICS, type TopicId } from "../constants/topics";

interface TopicSelectorProps {
  activeTopic: TopicId;
  onChange: (topic: TopicId) => void;
}

export function TopicSelector({ activeTopic, onChange }: TopicSelectorProps) {
  return (
    <div className="topic-scroll" aria-label="관심 분야">
      {TOPICS.map((topic) => (
        <button
          className="pill"
          key={topic.id}
          type="button"
          aria-pressed={activeTopic === topic.id}
          onClick={() => onChange(topic.id)}
        >
          {topic.label}
        </button>
      ))}
    </div>
  );
}
