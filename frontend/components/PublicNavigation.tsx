"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useRef, type ReactNode } from "react";

type PublicPath = "/" | "/signin" | "/signup";
type Transition = { skipTransition: () => void; ready: Promise<void>; finished: Promise<void> };
type PendingNavigation = { href: string; complete: () => void; transition: Transition };

const NavigationContext = createContext<(href: PublicPath) => boolean>(() => false);

/** Only the public marketing/auth links opt in; merchant workflows stay unchanged. */
export function PublicNavigationProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const pending = useRef<PendingNavigation | null>(null);

  useEffect(() => {
    if (pending.current?.href === pathname) pending.current.complete();
  }, [pathname]);

  useEffect(() => () => {
    pending.current?.transition.skipTransition();
    pending.current?.complete();
  }, []);

  const navigate = useCallback((href: PublicPath) => {
    if (href === pathname || window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
        typeof document.startViewTransition !== "function") return false;

    // A second click should never leave a frozen snapshot over the page.
    if (pending.current) {
      pending.current.transition.skipTransition();
      pending.current.complete();
      return false;
    }

    let timer: ReturnType<typeof setTimeout> | undefined;
    let resolveCommit: (() => void) | undefined;
    const committed = new Promise<void>((resolve) => { resolveCommit = resolve; });
    const complete = () => {
      clearTimeout(timer);
      resolveCommit?.();
    };

    try {
      const transition = document.startViewTransition(async () => {
        router.push(href);
        // Next navigation is asynchronous: snapshot the NEW page only after its DOM commits.
        await committed;
      });
      pending.current = { href, complete, transition };
      // Slow/offline navigation must remain usable instead of holding the old page indefinitely.
      timer = setTimeout(() => { transition.skipTransition(); complete(); }, 1800);
      void transition.ready.catch(() => { /* Unsupported snapshots degrade to normal navigation. */ });
      const cleanup = () => {
        complete();
        if (pending.current?.transition === transition) pending.current = null;
      };
      void transition.finished.then(cleanup, cleanup);
      return true;
    } catch {
      complete();
      return false;
    }
  }, [pathname, router]);

  return <NavigationContext.Provider value={navigate}>{children}</NavigationContext.Provider>;
}

export function PublicLink({ href, children, className }: {
  href: PublicPath;
  children: ReactNode;
  className?: string;
}) {
  const navigate = useContext(NavigationContext);
  return <Link href={href} className={className} onNavigate={(event) => {
    // onNavigate preserves new-tab/modifier clicks and ordinary anchor behavior.
    if (navigate(href)) event.preventDefault();
  }}>{children}</Link>;
}
