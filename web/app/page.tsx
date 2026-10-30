import { Dashboard } from "@/components/Dashboard";
import type { GoldPayload } from "@/lib/types";
import { readFile } from "fs/promises";
import path from "path";

async function loadGold(): Promise<GoldPayload> {
  const filePath = path.join(process.cwd(), "public", "data", "gold_metrics.json");
  const raw = await readFile(filePath, "utf8");
  return JSON.parse(raw) as GoldPayload;
}

export default async function HomePage() {
  const data = await loadGold();
  return <Dashboard data={data} />;
}
