import { PublicFeed } from "@/features/public-feed/components/public-feed";
import { parseInitialSelection } from "@/features/public-feed/lib/initial-selection";
import { getFallbackSnapshot, getPublicArchive } from "@/features/public-feed/server/get-public-snapshots";

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function HomePage({ searchParams }: PageProps) {
  const [archive, query] = await Promise.all([getPublicArchive(), searchParams]);
  const selection = parseInitialSelection(query);
  return <PublicFeed archive={archive} fallbackSnapshot={getFallbackSnapshot()} initialSelection={selection} />;
}
