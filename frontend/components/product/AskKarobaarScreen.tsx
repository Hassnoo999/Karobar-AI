"use client";

import { ArrowUp, ArrowUpRight, BookOpenCheck, CircleAlert, MessageCircleMore, RotateCcw, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { askQuestion } from "@/lib/api";
import { useProductData } from "./useProductData";
import { monthLabel, PageHeading } from "./ui";

type Message = {id: number; role: "user" | "assistant"; text: string; tool?: string; period?: string; provider?: string; answerSource?: string; error?: boolean};
const suggestions = [
  {title: "Outstanding udhaar", question: "Total udhaar kitna hai?"},
  {title: "Highest customer balance", question: "Sab se zyada udhaar kis ka hai?"},
  {title: "Sales this month", question: "Is month ki sales kitni hui?"},
  {title: "Compare monthly sales", question: "Is month aur pichle month ki sales ka comparison?"},
];
const toolNames: Record<string, string> = {total_outstanding: "All-time customer credit", top_debtor: "Highest outstanding customer", customer_outstanding: "Customer balance", monthly_sales: "Monthly sales", sales_comparison: "Monthly sales comparison"};

function answerPeriod(data: Record<string, unknown>) {
  if (typeof data.month === "string") return monthLabel(data.month);
  const current = data.current as Record<string, unknown> | undefined;
  const previous = data.previous as Record<string, unknown> | undefined;
  if (typeof current?.month === "string" && typeof previous?.month === "string") return monthLabel(previous.month) + " → " + monthLabel(current.month);
  return undefined;
}

export function AskKarobaarScreen() {
  const {connection} = useProductData();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [thinking, setThinking] = useState(false);
  const log = useRef<HTMLDivElement>(null);
  const sequence = useRef(0);
  const pending = useRef(false);
  const active = useRef(true);

  useEffect(() => {active.current = true; return () => {active.current = false;};}, []);
  useEffect(() => {
    const element = log.current;
    if (element) element.scrollTo({top: element.scrollHeight, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"});
  }, [messages, thinking]);

  async function send(question: string) {
    const text = question.trim();
    if (text.length < 2 || text.length > 500 || pending.current || connection !== "live") return;
    pending.current = true; setThinking(true); setInput("");
    setMessages(current => [...current, {id: ++sequence.current, role: "user", text}]);
    try {
      const result = await askQuestion(text);
      if (!active.current) return;
      setMessages(current => [...current, {id: ++sequence.current, role: "assistant", text: result.answer, tool: result.tool_used, period: answerPeriod(result.data), provider: result.provider, answerSource: result.answer_source}]);
    } catch (err) {
      if (!active.current) return;
      setMessages(current => [...current, {id: ++sequence.current, role: "assistant", text: err instanceof Error && err.message !== "Failed to fetch" ? err.message : "The assistant could not reach the API. No financial answer has been substituted. Try again when the connection is restored.", error: true}]);
    } finally {pending.current = false; if (active.current) setThinking(false);}
  }

  return <div className="flex h-[calc(100dvh-184px)] min-h-[440px] flex-col md:h-[calc(100dvh-192px)] lg:h-[calc(100dvh-144px)]">
    <PageHeading eyebrow="Your ledger, in plain language" title="Ask Karobaar." description="Ask about customer balances, monthly sales and sales comparisons." />
    <div className="ui-card grid min-h-0 flex-1 overflow-hidden lg:grid-cols-[1fr_260px]">
      <section className="flex min-h-0 min-w-0 flex-col" aria-label="Ledger conversation">
        <div className="flex items-center justify-between gap-3 border-b border-[#e7ede4] px-5 py-3.5">
          <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#e5f0dd] text-[#4d8151]"><MessageCircleMore size={18} strokeWidth={1.5} /></span><div><p className="text-xs font-semibold">Ledger assistant</p><p className="mt-0.5 text-[11px] text-[#627258]">Read-only · never changes your records</p></div></div>
          <button className="grid h-11 w-11 shrink-0 place-items-center rounded-lg text-[#627258] hover:bg-[#f0f5ed]" onClick={() => setMessages([])} disabled={!messages.length || thinking} aria-label="Clear chat" title="Clear chat"><RotateCcw size={16} /></button>
        </div>
        <div ref={log} role="log" aria-label="Chat messages" aria-live="polite" className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain p-4 md:p-6">
          {!messages.length ? <div className="flex h-full min-h-[180px] flex-col items-center justify-center px-2 text-center">
            <span className="grid h-14 w-14 place-items-center rounded-2xl border border-[#d7e6cc] bg-[#f1f7e9] text-[#627258]"><Sparkles size={24} strokeWidth={1.25} /></span>
            <h2 className="mt-5 !text-lg">Less searching. Clearer answers.</h2>
            <p className="mt-2 max-w-sm text-xs leading-6 text-[#627258]">Try “Ahmed ka udhaar kitna hai?”<br />English, Urdu and Roman Urdu are supported.</p>
            <div className="mt-5 flex flex-wrap justify-center gap-2 lg:hidden">{suggestions.slice(0, 2).map(item => <button key={item.title} onClick={() => void send(item.question)} disabled={connection !== "live" || thinking} className="min-h-10 rounded-lg border border-[#dce6d3] bg-[#f9fbf4] px-3 text-xs text-[#648357]">{item.title} <ArrowUpRight className="ml-1 inline" size={12} /></button>)}</div>
          </div> : messages.map(message => <div key={message.id} className={"flex " + (message.role === "user" ? "justify-end" : "justify-start")}>
            <article className={"max-w-[94%] rounded-2xl px-4 py-3.5 md:max-w-[86%] " + (message.role === "user" ? "rounded-br-md bg-[#234d33] text-white" : message.error ? "border border-[#e7cfb8] bg-[#fffaf1] text-[#927148]" : "rounded-bl-md border border-[#e3ebda] bg-[#f8faf3] text-[#425e39]")}>
              {message.role === "assistant" ? <p className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider opacity-65">{message.error ? <CircleAlert size={13} /> : <BookOpenCheck size={13} />}{message.error ? "Could not answer" : "Karobaar"}</p> : null}
              <p dir="auto" className="whitespace-pre-wrap break-words text-sm leading-7">{message.text}</p>
              {message.tool && message.tool !== "unsupported" ? <div className="mt-3 space-y-1 border-t border-[#dde6d3] pt-3 text-[11px] text-[#627258]"><p>{toolNames[message.tool] ?? message.tool} · confirmed ledger</p>{message.period ? <p>Period: {message.period}</p> : null}</div> : null}
              {message.answerSource === "deterministic_ledger" && message.tool !== "unsupported" ? <p className="mt-2 text-[11px] text-[#627258]">Ledger-calculated answer · {message.provider === "rules" ? "rule-based interpretation" : message.provider + " interpretation"}</p> : null}
              {message.provider === "demo" ? <p className="mt-3 rounded-lg bg-[#fff2d7] px-2.5 py-2 text-[11px] leading-5 text-[#967541]">Demo fallback interpreted this question. The answer uses ledger values, not AI-generated amounts.</p> : null}
              {message.tool === "unsupported" ? <p className="mt-3 text-[11px] opacity-70">Try a balance, monthly sales or sales-comparison question.</p> : null}
            </article>
          </div>)}
          {thinking ? <div role="status" className="flex items-center gap-2 text-xs text-[#627258]"><span className="h-3 w-3 animate-spin rounded-full border border-[#c4d7b6] border-t-[#55814e]" />Checking your confirmed ledger…</div> : null}
        </div>
        <form onSubmit={event => {event.preventDefault(); void send(input);}} className="border-t border-[#e7ede4] bg-white p-3 md:p-4">
          <label className="flex items-end gap-2 rounded-xl border border-[#d4e0cc] bg-[#fbfcf8] p-2 focus-within:border-[#7caf65]"><span className="sr-only">Your question</span><textarea rows={1} value={input} maxLength={500} onChange={event => setInput(event.target.value)} disabled={connection !== "live"} onKeyDown={event => {if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {event.preventDefault(); void send(input);}}} placeholder={connection === "live" ? "Ask a question about your ledger…" : "Connect the backend to ask questions"} className="max-h-24 min-h-[44px] min-w-0 flex-1 resize-none bg-transparent px-2 py-3 text-xs outline-none disabled:opacity-60" /><button disabled={input.trim().length < 2 || thinking || connection !== "live"} className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-[#326844] text-white" aria-label="Send question"><ArrowUp size={18} /></button></label>
          <p className="mt-2 text-center text-[11px] text-[#627258]">Enter to send · Shift + Enter for a new line · No loan approval or credit scoring</p>
        </form>
      </section>
      <aside className="hidden border-l border-[#e5ecdf] bg-[#f9fbf5] p-5 lg:block">
        <p className="ui-eyebrow !text-[11px]">A good place to start</p><h2 className="!text-sm">Ask something useful.</h2>
        <div className="mt-5 space-y-2">{suggestions.map(item => <button key={item.title} onClick={() => void send(item.question)} disabled={thinking || connection !== "live"} className="flex min-h-[58px] w-full items-center justify-between gap-2 rounded-xl border border-[#e3ebd8] bg-white px-3 py-3 text-left text-xs text-[#668458] hover:border-[#b5d09a]">{item.title}<ArrowUpRight size={14} className="shrink-0 text-[#627258]" /></button>)}</div>
        <div className="mt-8 border-t border-[#e0e8d6] pt-5"><BookOpenCheck size={18} className="text-[#627258]" /><p className="mt-3 text-xs font-medium">A grounded answer has a boundary.</p><p className="mt-2 text-xs leading-6 text-[#627258]">This version supports five ledger queries. Expenses, profit, cash balance and financing eligibility are not supported chat tools.</p><p className="mt-3 text-xs leading-6 text-[#627258]">Only confirmed entries count. Errors are shown honestly; they are not replaced with estimated answers.</p></div>
      </aside>
    </div>
  </div>;
}
