"use client";

import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState, type KeyboardEvent } from "react";
import DesktopWindow from "./DesktopWindow";
import GitHubPulse from "./GitHubPulse";
import { APP_COMMANDS, TERMINAL_GREETING_HINT, resolveTerminalCommand, type TerminalResult } from "./terminalContent";
import { PORTFOLIO_GREETING, PORTFOLIO_GREETING_ART } from "./asciiNameGeometry";
import { MAC_TERMINAL_PROMPT, terminalGridSize, type TerminalGrid } from "./macDesktopState";
import { terminalInitialFrame } from "./desktopState";

const COMMAND_LOADING_MS = 200;

function CommandSpinner() {
  return <p className="terminal-command-loading" role="status" aria-label="Running command">
    <span className="terminal-command-spinner" aria-hidden="true"><span>{"-\n\\\n|\n/"}</span></span>
  </p>;
}

type SessionHandle = { run: (command: string) => void; focus: () => void };
export type TerminalHandle = SessionHandle;
type Props = {
  instance: number;
  mobileLayout?: boolean;
  active: boolean; foreground: boolean; focusSession: boolean; minimized: boolean; zIndex: number; initialCommand?: string;
  onActivate: () => void; onMinimize: () => void; onClose: () => void; onExit: () => void;
};

const TerminalSession = forwardRef<SessionHandle, { active: boolean; focusOnActivate: boolean; mobileLayout?: boolean; initialCommand?: string; id: number; onGridChange: (grid: TerminalGrid) => void; onExit: () => void }>(function TerminalSession({ active, focusOnActivate, mobileLayout, initialCommand, id, onGridChange, onExit }, ref) {
  const [input, setInput] = useState("");
  const [transcript, setTranscript] = useState<TerminalResult[]>([]);
  const [pendingCommand, setPendingCommand] = useState<string | null>(initialCommand?.trim() ? initialCommand : null);
  const pendingRef = useRef(pendingCommand);
  const commandTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [history, setHistory] = useState<string[]>(initialCommand ? [initialCommand] : []);
  const [showWelcome, setShowWelcome] = useState(true);
  const [stopped, setStopped] = useState(false);
  const [caret, setCaret] = useState({ column: 0, scroll: 0, visible: true });
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const activeRef = useRef(active);
  activeRef.current = active;
  const bodyRef = useRef<HTMLDivElement>(null);
  const contentsRef = useRef<HTMLDivElement>(null);
  const cellProbeRef = useRef<HTMLSpanElement>(null);
  const followTail = useRef(true);
  const lastScrollTop = useRef(0);
  const historyIndex = useRef<number | null>(null);
  const draft = useRef("");
  const completion = useRef<{ seed: string; index: number } | null>(null);

  function syncCaret() {
    const field = inputRef.current;
    if (field) setCaret({ column: field.selectionStart ?? field.value.length, scroll: field.scrollLeft, visible: field.selectionStart === field.selectionEnd });
  }
  function focus() { if (activeRef.current) inputRef.current?.focus({ preventScroll: true }); }
  function replaceInput(value: string) {
    setInput(value);
    window.requestAnimationFrame(() => {
      inputRef.current?.setSelectionRange(value.length, value.length);
      syncCaret();
    });
  }
  function run(command: string) {
    // Lock synchronously as menu actions can arrive before React renders busy state.
    if (pendingRef.current !== null) {
      if (command.trim().toLowerCase() !== "clear") return;
      if (pendingRef.current.trim().toLowerCase() === "clear") return;
      if (commandTimer.current !== null) clearTimeout(commandTimer.current);
      commandTimer.current = null;
    }
    followTail.current = true;
    completion.current = null;
    historyIndex.current = null;
    if (command.trim()) setHistory((current) => [...current, command.trim()]);
    if (command.trim()) {
      pendingRef.current = command;
      setPendingCommand(command);
    } else setTranscript((current) => [...current, { command: "", lines: [] }]);
    setStopped(false);
    replaceInput("");
    window.requestAnimationFrame(focus);
  }
  useImperativeHandle(ref, () => ({ run, focus }));

  const finishCommand = useRef<((command: string) => void) | null>(null);
  finishCommand.current = (command: string) => {
    const result = resolveTerminalCommand(command);
    pendingRef.current = null;
    setPendingCommand(null);
    if (result?.exit) { onExit(); return; }
    if (result?.clear) { setTranscript([]); setShowWelcome(false); }
    else if (result) setTranscript((current) => [...current, result]);
    window.requestAnimationFrame(focus);
  };
  useEffect(() => {
    if (pendingCommand === null) return;
    commandTimer.current = setTimeout(() => {
      commandTimer.current = null;
      finishCommand.current?.(pendingCommand);
    }, COMMAND_LOADING_MS);
    return () => { if (commandTimer.current !== null) clearTimeout(commandTimer.current); };
  }, [pendingCommand]);

  useEffect(() => {
    // On the phone review, entering the monitor must not immediately summon
    // the software keyboard. An intentional tap in the terminal still focuses it.
    if (mobileLayout && window.matchMedia("(pointer: coarse)").matches) return;
    if (focusOnActivate) inputRef.current?.focus({ preventScroll: true });
  }, [focusOnActivate, mobileLayout]);
  useEffect(() => {
    const body = bodyRef.current;
    const contents = contentsRef.current;
    const probe = cellProbeRef.current;
    if (!body || !contents || !probe) return;
    let cellWidth = 0;
    let lineHeight = 0;
    const observer = new ResizeObserver((entries) => {
      // Content-box measurements stay accurate during window animations and
      // update when the monospace font, zoom, or available viewport changes.
      for (const entry of entries) if (entry.target === probe) {
        cellWidth = entry.contentRect.width / 10;
        lineHeight = entry.contentRect.height;
      }
      const styles = getComputedStyle(body);
      const pixels = (value: string) => Number.parseFloat(value) || 0;
      const grid = terminalGridSize(
        body.clientWidth - pixels(styles.paddingLeft) - pixels(styles.paddingRight),
        body.clientHeight - pixels(styles.paddingTop) - pixels(styles.paddingBottom),
        cellWidth, lineHeight,
      );
      if (grid) onGridChange(grid);
      if (followTail.current) {
        body.scrollTop = body.scrollHeight;
        lastScrollTop.current = body.scrollTop;
      }
    });
    observer.observe(contents);
    observer.observe(body);
    observer.observe(probe);
    return () => observer.disconnect();
  }, [onGridChange]);

  function handleKey(event: KeyboardEvent<HTMLInputElement>) {
    if (event.nativeEvent.isComposing) return;
    if (pendingRef.current !== null && !(event.ctrlKey && ["c", "l"].includes(event.key.toLowerCase()))) {
      if (!event.ctrlKey && !event.metaKey) event.preventDefault();
      return;
    }
    const plainKey = !event.ctrlKey && !event.metaKey && !event.altKey;
    if (plainKey && (event.key === "ArrowUp" || event.key === "ArrowDown")) {
      event.preventDefault();
      if (!history.length) return;
      if (historyIndex.current === null) draft.current = input;
      const direction = event.key === "ArrowUp" ? -1 : 1;
      const index = Math.max(0, Math.min(history.length, (historyIndex.current ?? history.length) + direction));
      historyIndex.current = index === history.length ? null : index;
      completion.current = null;
      replaceInput(index === history.length ? draft.current : history[index]);
    } else if (plainKey && event.key === "Tab") {
      event.preventDefault();
      const seed = completion.current?.seed ?? input.toLowerCase();
      const choices = [...Object.values(APP_COMMANDS), "clear", "exit"].filter((command) => command.startsWith(seed));
      if (!choices.length) return;
      const index = ((completion.current?.index ?? (event.shiftKey ? 0 : -1)) + (event.shiftKey ? -1 : 1) + choices.length) % choices.length;
      completion.current = { seed, index };
      replaceInput(choices[index]);
    } else if (event.ctrlKey && event.key.toLowerCase() === "c") {
      if (window.getSelection()?.toString() || inputRef.current?.selectionStart !== inputRef.current?.selectionEnd) return;
      event.preventDefault();
      setStopped(true);
      const interrupted = pendingRef.current ?? input;
      if (commandTimer.current !== null) clearTimeout(commandTimer.current);
      commandTimer.current = null;
      pendingRef.current = null;
      setPendingCommand(null);
      setTranscript((current) => [...current, { command: `${interrupted}^C`, lines: [] }]);
      replaceInput("");
      historyIndex.current = null;
      completion.current = null;
      followTail.current = true;
    } else if (event.ctrlKey && event.key.toLowerCase() === "l") {
      event.preventDefault(); run("clear");
    } else if (event.key === "Escape") {
      replaceInput(""); historyIndex.current = null; completion.current = null;
    } else if (event.key !== "Shift") completion.current = null;
  }

  return <div
    className="win-terminal-session windows-terminal-body"
    ref={bodyRef}
    onScroll={() => {
      const body = bodyRef.current;
      if (!body) return;
      // Loading output can grow after a programmatic scroll. Only an actual
      // upward scroll should stop following it, not the new distance to bottom.
      if (body.scrollHeight - body.clientHeight - body.scrollTop < 32) followTail.current = true;
      else if (body.scrollTop < lastScrollTop.current - 1) followTail.current = false;
      lastScrollTop.current = body.scrollTop;
    }}
    onClick={(event) => { if (!(event.target as HTMLElement).closest("input, a, button") && !window.getSelection()?.toString()) focus(); }}
  >
    <span ref={cellProbeRef} className="terminal-cell-probe" aria-hidden="true">0000000000</span>
    <div ref={contentsRef}>
      <div role="log" aria-live={active ? "polite" : "off"} aria-relevant="additions">
        {showWelcome && <>
          <pre className="windows-terminal-name-art" role="img" aria-label={PORTFOLIO_GREETING}>{PORTFOLIO_GREETING_ART}</pre>
          {mobileLayout && <p className="mobile-terminal-greeting">Brian Zeng’s Portfolio</p>}<br />
          <p>{TERMINAL_GREETING_HINT}</p><br />
        </>}
        {transcript.map((entry, index) => <div className="windows-terminal-entry" key={index}>
          <p>{MAC_TERMINAL_PROMPT}{entry.command}</p>
          {entry.lines.map((line, lineIndex) => {
            const link = entry.links?.find((item) => line.includes(item.text));
            if (!link) return <p key={lineIndex}>{line || "\u00a0"}</p>;
            const start = line.indexOf(link.text);
            return <p key={lineIndex}>{line.slice(0, start)}<a href={link.href} target={link.href.startsWith("https:") ? "_blank" : undefined} rel="noopener noreferrer">{link.text}</a>{line.slice(start + link.text.length)}</p>;
          })}
          {entry.pulse && <GitHubPulse variant="terminal" active={active && !stopped && index === transcript.length - 1} />}
          <br />
        </div>)}
      </div>
      {pendingCommand !== null && <div className="terminal-pending-command">
        <p>{MAC_TERMINAL_PROMPT}{pendingCommand}</p>
        <CommandSpinner />
      </div>}
      <form className="windows-terminal-prompt" onSubmit={(event) => { event.preventDefault(); run(input); }}>
        <label htmlFor={`terminal-command-${id}`}>{pendingCommand === null ? MAC_TERMINAL_PROMPT : ""}</label>
        <span className="windows-terminal-input-wrap">
          <input id={`terminal-command-${id}`} ref={inputRef} aria-label="Terminal command" value={input}
            readOnly={pendingCommand !== null} aria-busy={pendingCommand !== null}
            onChange={(event) => { setInput(event.target.value); historyIndex.current = null; completion.current = null; syncCaret(); }}
            onKeyDown={handleKey} onKeyUp={syncCaret} onSelect={syncCaret} onScroll={syncCaret}
            onFocus={() => { setFocused(true); syncCaret(); }} onBlur={() => setFocused(false)}
            autoCapitalize="none" autoComplete="off" spellCheck={false} />
          {pendingCommand === null && active && focused && caret.visible && <span className="windows-terminal-caret" aria-hidden="true" style={{ left: `calc(${caret.column}ch - ${caret.scroll}px)` }}>_</span>}
        </span>
      </form>
    </div>
  </div>;
});

const DesktopTerminal = forwardRef<TerminalHandle, Props>(function DesktopTerminal(props, ref) {
  const session = useRef<SessionHandle>(null);
  const [grid, setGrid] = useState<TerminalGrid | null>(null);
  const updateGrid = useCallback((next: TerminalGrid) => {
    setGrid((current) => current?.columns === next.columns && current.rows === next.rows ? current : next);
  }, []);
  useImperativeHandle(ref, () => ({
    run: (command) => session.current?.run(command),
    focus: () => session.current?.focus(),
  }));

  function terminalKeys(event: KeyboardEvent<HTMLDivElement>) {
    if (event.metaKey && event.key.toLowerCase() === "w") { event.preventDefault(); props.onClose(); }
    if (event.metaKey && event.key.toLowerCase() === "k") { event.preventDefault(); session.current?.run("clear"); }
  }

  return <div className="win-terminal-host" onKeyDown={terminalKeys}>
    <DesktopWindow {...props} initialFrame={terminalInitialFrame(props.instance)} className="mac-terminal-window" title={`Terminal ${props.instance}`} titlebar={
      <div className="mac-window-heading"><img className="mac-title-folder" src="/macos-icons/folder.png" alt="" draggable={false} /><span>brian — -zsh{grid && <> — <span className="mac-terminal-grid" aria-label={`${grid.columns} columns by ${grid.rows} rows`}>{grid.columns}×{grid.rows}</span></>}</span></div>
    }>
      <div className="win-terminal-panel">
        <TerminalSession ref={session} id={props.instance} initialCommand={props.initialCommand} mobileLayout={props.mobileLayout}
          onGridChange={updateGrid} onExit={props.onExit}
          active={props.active && !props.minimized} focusOnActivate={props.focusSession && !props.minimized} />
      </div>
    </DesktopWindow>
  </div>;
});

export default DesktopTerminal;
