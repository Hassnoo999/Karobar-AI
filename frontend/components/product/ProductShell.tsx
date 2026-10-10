"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ArrowUpRight, BookOpenCheck, CircleHelp, LayoutDashboard, LogOut, Menu, MessageCircleMore, Mic2, RefreshCw, ShieldCheck, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { BrandLogo } from "@/components/BrandLogo";
import { useAuth } from "@/components/SupabaseProvider";
import { NavigationProgress } from "./NavigationProgress";
import { useProductData } from "./useProductData";
import { monthLabel } from "./ui";

const navigation = [
  {href: "/dashboard", label: "Overview", short: "Overview", icon: LayoutDashboard},
  {href: "/record", label: "Record transaction", short: "Record", icon: Mic2},
  {href: "/ledger", label: "Ledger & udhaar", short: "Ledger", icon: BookOpenCheck},
  {href: "/ask", label: "Ask Karobaar", short: "Ask", icon: MessageCircleMore},
  {href: "/evidence", label: "Evidence & readiness", short: "Evidence", icon: ShieldCheck},
];

function NavLinks({onSelect}: {onSelect?: () => void}) {
  const pathname = usePathname();
  return <nav aria-label="Primary navigation" className="space-y-1.5">{navigation.map(({href, label, icon: Icon}) => <Link key={href} href={href} onClick={onSelect} aria-current={pathname === href ? "page" : undefined} className={"flex min-h-12 items-center gap-3 rounded-xl px-3 text-[13px] transition-colors " + (pathname === href ? "bg-[#d9f3df] font-semibold text-[#153d2a]" : "text-[#afc5b6] hover:bg-white/[.07] hover:text-white")}><Icon size={19} strokeWidth={1.7} />{label}</Link>)}</nav>;
}

export function ProductShell({children}: {children: React.ReactNode}) {
  const pathname = usePathname();
  const router = useRouter();
  const dialog = useRef<HTMLDialogElement>(null);
  const {user, signOut, authEnabled, loading} = useAuth();
  const {connection, dashboard, source_counts, error, refreshing, refresh} = useProductData();
  const current = navigation.find(item => item.href === pathname)?.label ?? "Workspace";
  const storeName = typeof user?.user_metadata?.business_name === "string" ? user.user_metadata.business_name : authEnabled ? "Your business" : "Local workspace";
  const initials = storeName.split(" ").filter(Boolean).map((word: string) => word[0]).join("").slice(0, 2).toUpperCase();
  const sampleLedger = (source_counts?.seed ?? 0) > 0;

  useEffect(() => {
    if (!loading && authEnabled && !user) router.replace("/signin");
  }, [authEnabled, loading, router, user]);

  async function leave() {
    if (authEnabled) await signOut();
    router.push(authEnabled ? "/signin" : "/");
  }

  if (authEnabled && (loading || !user)) return <div className="grid min-h-screen place-items-center bg-[#f3f6f2]"><p className="text-sm text-[#446550]">Checking your session…</p></div>;

  const sidebar = <>
    <Link href="/" className="mb-9 block px-2" aria-label="Karobaar AI home"><BrandLogo inverse /></Link>
    <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[.15em] text-[#809e8c]">Your workspace</p>
    <NavLinks onSelect={() => dialog.current?.close()} />
    <div className="mt-auto pt-8">
      <div className="mb-5 rounded-xl border border-white/10 bg-white/[.04] p-4"><ShieldCheck size={20} className="mb-3 text-[#a3d5b0]" /><p className="text-xs font-semibold text-[#d5e5da]">Your records. Your decision.</p><p className="mt-2 text-[11px] leading-5 text-[#96b2a1]">AI proposes an entry. You review it before it reaches the ledger.</p></div>
      <Link href="/#process" className="flex min-h-11 items-center gap-3 px-3 text-xs text-[#a9c0b0]"><CircleHelp size={17} /> How it works <ArrowUpRight size={13} className="ml-auto" /></Link>
      <button onClick={leave} className="flex min-h-11 w-full items-center gap-3 px-3 text-xs text-[#a9c0b0]"><LogOut size={17} />{authEnabled ? "Sign out" : "Close workspace"}</button>
    </div>
  </>;

  return <div className="product-shell min-h-screen">
    <NavigationProgress />
    <a href="#workspace-content" className="sr-only z-[100] rounded-lg bg-white p-3 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[232px] flex-col bg-[#102c21] px-4 pb-5 pt-8 lg:flex">{sidebar}</aside>
    <div className="min-h-screen lg:pl-[232px]">
      <header className="sticky top-0 z-30 flex h-[72px] items-center gap-3 border-b border-[#e0e8e2] bg-[#fafcf9]/95 px-4 backdrop-blur md:px-8">
        <button className="grid h-11 w-11 place-items-center rounded-xl text-[#31563e] lg:hidden" onClick={() => dialog.current?.showModal()} aria-label="Open navigation"><Menu size={22} /></button>
        <div className="min-w-0"><p className="truncate text-[13px] font-semibold">{storeName}</p><p className="mt-0.5 text-[11px] text-[#7b8c80]">{current}</p></div>
        <div className="ml-auto flex items-center gap-3">
          <span className="hidden text-xs text-[#728378] xl:block">{monthLabel(dashboard?.month)}</span>
          <span className={"ui-badge " + (connection === "error" || sampleLedger ? "badge-amber" : "badge-neutral")}><i className={"h-1.5 w-1.5 rounded-full " + (connection === "live" ? "bg-[#3d9960]" : connection === "error" ? "bg-[#bc8532]" : "bg-[#96a79a]")} /><span>{connection === "checking" ? "Connecting" : connection === "error" ? "Offline" : sampleLedger ? "Sample ledger" : "API connected"}</span></span>
          {pathname !== "/record" ? <Link href="/record" className="ui-button-primary hidden sm:inline-flex"><Mic2 size={16} /> Record</Link> : null}
          <span className="hidden h-9 w-9 place-items-center rounded-full border border-[#d8e5dc] bg-[#e6eee7] text-[11px] font-semibold sm:grid">{initials}</span>
        </div>
      </header>
      <main id="workspace-content" key={pathname} className="route-page-enter mx-auto max-w-[1500px] px-4 pb-[100px] pt-6 md:px-8 md:pt-8 lg:pb-10">
        {connection === "error" ? <div role="alert" className="mb-6 flex flex-wrap items-center gap-3 rounded-xl border border-[#eddbb8] bg-[#fffaed] p-4"><div className="min-w-[180px] flex-1"><p className="text-sm font-semibold text-[#795724]">Connection needs attention</p><p className="mt-1 text-xs leading-5 text-[#876c42]">{error} Any previously loaded totals may be out of date.</p></div><button onClick={() => void refresh()} disabled={refreshing} className="ui-button-secondary"><RefreshCw size={14} className={refreshing ? "animate-spin" : ""} /> Retry</button></div> : null}
        {children}
      </main>
    </div>
    <dialog ref={dialog} aria-label="Workspace navigation" onClick={event => {if (event.target === event.currentTarget) dialog.current?.close();}} className="fixed inset-y-0 left-0 m-0 h-[100dvh] max-h-none w-[min(320px,90vw)] max-w-none border-0 bg-[#102c21] p-5 text-white backdrop:bg-[#0b251d]/50"><div className="mb-5 flex justify-end"><button onClick={() => dialog.current?.close()} aria-label="Close navigation" className="grid h-11 w-11 place-items-center rounded-xl bg-white/10"><X size={20} /></button></div><div className="flex min-h-[calc(100dvh-110px)] flex-col">{sidebar}</div></dialog>
    <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-[#dce6df] bg-[#fcfdfa] pb-[env(safe-area-inset-bottom)] shadow-[0_-4px_24px_rgba(16,44,33,.04)] lg:hidden" aria-label="Mobile navigation">{navigation.map(({href, short, icon: Icon}) => <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined} className={"flex min-h-[68px] flex-col items-center justify-center gap-1.5 text-[10px] " + (pathname === href ? "font-semibold text-[#145537]" : "text-[#77897b]")}><span className={"rounded-lg px-3 py-1 " + (pathname === href ? "bg-[#e3f0e4]" : "")}><Icon size={19} strokeWidth={pathname === href ? 2 : 1.6} /></span>{short}</Link>)}</nav>
  </div>;
}
