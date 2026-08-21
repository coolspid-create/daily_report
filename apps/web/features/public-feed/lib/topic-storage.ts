import { TOPIC_IDS, type TopicId } from "../constants/topics";

export const TOPIC_STORAGE_KEY = "today-public-report:topic";
const subscribers = new Set<() => void>();

export function readStoredTopic(storage: Pick<Storage, "getItem">): TopicId | null {
  const value = storage.getItem(TOPIC_STORAGE_KEY);
  return value && TOPIC_IDS.has(value as TopicId) ? (value as TopicId) : null;
}

export function storeTopic(storage: Pick<Storage, "setItem">, topic: TopicId): void {
  storage.setItem(TOPIC_STORAGE_KEY, topic);
  subscribers.forEach((subscriber) => subscriber());
}

export function subscribeToStoredTopic(onChange: () => void): () => void {
  const onStorage = (event: StorageEvent) => {
    if (event.key === TOPIC_STORAGE_KEY) onChange();
  };
  subscribers.add(onChange);
  window.addEventListener("storage", onStorage);
  return () => {
    subscribers.delete(onChange);
    window.removeEventListener("storage", onStorage);
  };
}
