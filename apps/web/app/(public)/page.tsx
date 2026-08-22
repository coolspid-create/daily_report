import { PublicFeed } from "@/features/public-feed/components/public-feed";
import { parseInitialSelection } from "@/features/public-feed/lib/initial-selection";
import { getFallbackSnapshot, getPublicArchive } from "@/features/public-feed/server/get-public-snapshots";

export const revalidate = 3600;

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function HomePage({ searchParams }: PageProps) {
  const query = await searchParams;
  const selection = parseInitialSelection(query);
  const archive = await getPublicArchive(selection.archiveDate);
  return <PublicFeed archive={archive} fallbackSnapshot={getFallbackSnapshot()} initialSelection={selection} />;
}
