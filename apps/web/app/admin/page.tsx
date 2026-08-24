import { redirect } from "next/navigation";
import { getAdminUser } from "@/lib/auth/admin-session";
import { getReviewItems } from "@/features/admin-review/server/get-review-items";
import { getSourceHealth } from "@/features/source-health/server/get-source-health";
import { ReviewWorkbench } from "@/features/admin-review/components/review-workbench";
import { getAutomationStatus } from "@/features/admin-review/server/get-automation-status";
import { getPublicationHistory, getStoredDocuments } from "@/features/admin-review/server/get-review-history";

export default async function AdminPage() {
  const user = await getAdminUser();
  if (!user) redirect("/admin/login");
  const [items, sources, automation, publications, storedDocuments] = await Promise.all([
    getReviewItems(), getSourceHealth(), getAutomationStatus(), getPublicationHistory(), getStoredDocuments(),
  ]);
  return <ReviewWorkbench items={items} sources={sources} automation={automation} publications={publications} storedDocuments={storedDocuments} eligibilityNow={new Date().toISOString()} />;
}
