import type { DeliveryMode, ReportFile } from "../types/public-report";

export interface PrimaryAction {
  label: string;
  url: string;
  download: boolean;
}

const DOWNLOAD_MODES = new Set<DeliveryMode>(["DIRECT_OFFICIAL_FILE", "MIRRORED_ALLOWED"]);

export function primaryAction(file: ReportFile): PrimaryAction | null {
  if (DOWNLOAD_MODES.has(file.deliveryMode) && file.downloadUrl) {
    const format = file.format?.toUpperCase();
    const label = format === "HWP" ? "HWP ↓" : "PDF ↓";
    return { label, url: file.downloadUrl, download: true };
  }
  return null;
}
