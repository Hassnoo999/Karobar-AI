"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { getCombinedData, type CombinedDataResponse } from "@/lib/api";
import { useAuth } from "@/components/SupabaseProvider";

const emptyData: CombinedDataResponse = {
  summary: {total_sales: 0, total_expenses: 0, total_receivables: 0, total_payables: 0, total_recovered: 0, net_cash: 0, record_count: 0, recent_events: []},
  events: [], customers: [], source_counts: {},
  intelligence: {evidence_profile: {documentation_coverage: "No records", income_consistency: "No records", receivable_discipline: "No credit records", expense_pattern: "No records", customer_concentration: "No credit records", ledger_depth: "No records", trust_notes: []}, financing_matches: []},
};
type Connection = "checking" | "live" | "error";
type ProductData = CombinedDataResponse & {connection: Connection; refreshing: boolean; error: string; refresh: () => Promise<void>};
const ProductContext = createContext<ProductData | null>(null);

export function ProductDataProvider({ children }: { children: React.ReactNode }) {
  const {user, loading, authEnabled} = useAuth();
  const identity = authEnabled ? user?.id ?? "signed-out" : "local";
  const [snapshot, setSnapshot] = useState({owner: identity, data: emptyData});
  const [connection, setConnection] = useState<Connection>("checking");
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const generation = useRef(0);

  const refresh = useCallback(async () => {
    if (loading || (authEnabled && !user)) return;
    const request = ++generation.current;
    setRefreshing(true);
    setError("");
    try {
      const data = await getCombinedData();
      if (request !== generation.current) return;
      setSnapshot({owner: identity, data});
      setConnection("live");
    } catch (err) {
      if (request !== generation.current) return;
      setError(err instanceof Error && err.message !== "Failed to fetch" ? err.message : "The backend could not be reached. Your records have not been changed.");
      setConnection("error");
    } finally {
      if (request === generation.current) setRefreshing(false);
    }
  }, [identity, loading, authEnabled, user]);

  useEffect(() => {
    setSnapshot({owner: identity, data: emptyData});
    setConnection("checking");
    setError("");
    void refresh();
    return () => { generation.current += 1; };
  }, [identity, refresh]);

  const data = snapshot.owner === identity ? snapshot.data : emptyData;
  // Remount private screen state too: old chat messages/drafts must never carry
  // across account switches, even though the shared snapshot already clears.
  return <ProductContext.Provider key={identity} value={{...data, connection, refreshing, error, refresh}}>{children}</ProductContext.Provider>;
}

export function useProductData() {
  const value = useContext(ProductContext);
  if (!value) throw new Error("ProductDataProvider is missing");
  return value;
}
