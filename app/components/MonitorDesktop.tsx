"use client";

import {
  useRef,
  useState,
  type FormEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import { ChevronUp12Regular } from "@fluentui/react-icons/svg/chevron-up";
import { Code24Regular } from "@fluentui/react-icons/svg/code";
import { Dismiss16Regular } from "@fluentui/react-icons/svg/dismiss";
import { Folder24Regular } from "@fluentui/react-icons/svg/folder";
import { Globe24Regular } from "@fluentui/react-icons/svg/globe";
import { Mail24Regular } from "@fluentui/react-icons/svg/mail";
import { Person24Regular } from "@fluentui/react-icons/svg/person";
import { QuestionCircle24Regular } from "@fluentui/react-icons/svg/question-circle";
import { Recycle20Regular } from "@fluentui/react-icons/svg/recycle";
import { Search24Regular } from "@fluentui/react-icons/svg/search";
import { ShoppingBag24Regular } from "@fluentui/react-icons/svg/shopping-bag";
import { Speaker220Regular } from "@fluentui/react-icons/svg/speaker";
import { Square16Regular } from "@fluentui/react-icons/svg/square";
import { Subtract16Regular } from "@fluentui/react-icons/svg/subtract";
import { WeatherPartlyCloudyNight24Regular } from "@fluentui/react-icons/svg/weather-partly-cloudy-night";
import { Wifi420Regular } from "@fluentui/react-icons/svg/wifi";
import { WindowConsole20Regular } from "@fluentui/react-icons/svg/window-console";
import { WindowMultiple24Regular } from "@fluentui/react-icons/svg/window-multiple";
import GitHubPulse from "./GitHubPulse";

type DesktopCommand = "help" | "github" | "about" | "contact";
type WindowId = "terminal" | DesktopCommand;

type TranscriptEntry = {
  command: string;
  lines: string[];
};

type WindowFrame = {
  height: number;
  width: number;
  x: number;
  y: number;
  z: number;
};

const DESKTOP_ITEMS = [
  { command: "help", Icon: QuestionCircle24Regular, label: "Help" },
  { command: "github", Icon: Code24Regular, label: "GitHub Pulse" },
  { command: "about", Icon: Person24Regular, label: "About Brian" },
  { command: "contact", Icon: Mail24Regular, label: "Contact" },
] as const;

const RESPONSES: Record<DesktopCommand, string[]> = {
  help: [
    "Available commands:",
    "  help      show this command list",
    "  github    open GitHub Pulse",
    "  about     open About Brian",
    "  contact   open Contact",
    "  clear     clear the terminal",
  ],
  github: ["GitHub Pulse opened in a new window."],
  about: ["About Brian opened in a new window."],
  contact: ["Contact opened in a new window."],
};

const INITIAL_FRAMES: Record<WindowId, WindowFrame> = {
  terminal: { x: .22, y: .105, width: .59, height: .61, z: 10 },
  help: { x: .12, y: .16, width: .29, height: .42, z: 11 },
  github: { x: .31, y: .08, width: .53, height: .76, z: 12 },
  about: { x: .27, y: .17, width: .39, height: .47, z: 13 },
  contact: { x: .40, y: .23, width: .31, height: .36, z: 14 },
};

const MINIMUM_SIZE: Record<WindowId, { height: number; width: number }> = {
  terminal: { width: .34, height: .32 },
  help: { width: .22, height: .27 },
  github: { width: .36, height: .42 },
  about: { width: .28, height: .31 },
  contact: { width: .23, height: .25 },
};

function isDesktopCommand(value: string): value is DesktopCommand {
  return DESKTOP_ITEMS.some((item) => item.command === value);
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

function frameStyle(frame: WindowFrame) {
  return {
    height: `${frame.height * 100}%`,
    left: `${frame.x * 100}%`,
    top: `${frame.y * 100}%`,
    width: `${frame.width * 100}%`,
    zIndex: frame.z,
  };
}

type AppWindowProps = {
  children: ReactNode;
  className?: string;
  frame: WindowFrame;
  Icon: typeof QuestionCircle24Regular;
  id: DesktopCommand;
  onBringToFront: (id: WindowId) => void;
  onClose: (id: DesktopCommand) => void;
  onDragStart: (event: ReactPointerEvent<HTMLElement>, id: WindowId) => void;
  onMaximize: (id: WindowId) => void;
  onResizeStart: (event: ReactPointerEvent<HTMLElement>, id: WindowId) => void;
  title: string;
};

function AppWindow({
  children,
  className = "",
  frame,
  Icon,
  id,
  onBringToFront,
  onClose,
  onDragStart,
  onMaximize,
  onResizeStart,
  title,
}: AppWindowProps) {
  return (
    <section
      className={`windows-app-window ${className}`}
      style={frameStyle(frame)}
      aria-label={title}
      onPointerDown={() => onBringToFront(id)}
    >
      <header className="windows-app-titlebar" onPointerDown={(event) => onDragStart(event, id)}>
        <span className="windows-app-title"><Icon aria-hidden="true" />{title}</span>
        <div className="windows-caption-controls">
          <button type="button" onPointerDown={(event) => event.stopPropagation()} onClick={() => onClose(id)} aria-label={`Minimize ${title}`}><Subtract16Regular /></button>
          <button type="button" onPointerDown={(event) => event.stopPropagation()} onClick={() => onMaximize(id)} aria-label={`Maximize ${title}`}><Square16Regular /></button>
          <button className="windows-caption-close" type="button" onPointerDown={(event) => event.stopPropagation()} onClick={() => onClose(id)} aria-label={`Close ${title}`}><Dismiss16Regular /></button>
        </div>
      </header>
      <div className="windows-app-body">{children}</div>
      <button
        className="windows-resize-handle"
        type="button"
        aria-label={`Resize ${title}`}
        onPointerDown={(event) => onResizeStart(event, id)}
      />
    </section>
  );
}

export default function MonitorDesktop() {
  const desktopRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const zIndexRef = useRef(20);
  const [input, setInput] = useState("");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [openApps, setOpenApps] = useState<Record<DesktopCommand, boolean>>({
    help: false,
    github: false,
    about: false,
    contact: false,
  });
  const [frames, setFrames] = useState<Record<WindowId, WindowFrame>>(INITIAL_FRAMES);

  function bringToFront(id: WindowId) {
    const z = ++zIndexRef.current;
    setFrames((current) => ({ ...current, [id]: { ...current[id], z } }));
  }

  function openApp(id: DesktopCommand) {
    setOpenApps((current) => ({ ...current, [id]: true }));
    bringToFront(id);
  }

  function closeApp(id: DesktopCommand) {
    setOpenApps((current) => ({ ...current, [id]: false }));
  }

  function openTerminal() {
    setTerminalOpen(true);
    bringToFront("terminal");
    window.setTimeout(() => inputRef.current?.focus(), 0);
  }

  function maximizeWindow(id: WindowId) {
    bringToFront(id);
    setFrames((current) => ({
      ...current,
      [id]: { ...current[id], x: .012, y: .012, width: .976, height: .925 },
    }));
  }

  function beginWindowAction(
    event: ReactPointerEvent<HTMLElement>,
    id: WindowId,
    mode: "drag" | "resize",
  ) {
    if (event.button !== 0) return;
    if (mode === "drag" && (event.target as HTMLElement).closest("button")) return;

    const desktop = desktopRef.current;
    if (!desktop) return;

    event.preventDefault();
    bringToFront(id);
    const bounds = desktop.getBoundingClientRect();
    const startFrame = frames[id];
    const startX = event.clientX;
    const startY = event.clientY;

    function move(moveEvent: PointerEvent) {
      const deltaX = (moveEvent.clientX - startX) / bounds.width;
      const deltaY = (moveEvent.clientY - startY) / bounds.height;

      setFrames((current) => {
        if (mode === "drag") {
          return {
            ...current,
            [id]: {
              ...current[id],
              x: clamp(startFrame.x + deltaX, 0, 1 - startFrame.width),
              y: clamp(startFrame.y + deltaY, 0, .955 - startFrame.height),
            },
          };
        }

        const minimum = MINIMUM_SIZE[id];
        return {
          ...current,
          [id]: {
            ...current[id],
            width: clamp(startFrame.width + deltaX, minimum.width, 1 - startFrame.x),
            height: clamp(startFrame.height + deltaY, minimum.height, .955 - startFrame.y),
          },
        };
      });
    }

    function stop() {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
      window.removeEventListener("pointercancel", stop);
    }

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop);
    window.addEventListener("pointercancel", stop);
  }

  function runCommand(rawValue: string) {
    const command = rawValue.trim().toLowerCase();
    if (!command) return;

    if (command === "clear") {
      setTranscript([]);
      setInput("");
      return;
    }

    const lines = isDesktopCommand(command)
      ? RESPONSES[command]
      : [`'${command}' is not recognized as a command.`, "Type 'help' to see available commands."];

    setTranscript((current) => [...current, { command, lines }]);
    setInput("");
    if (isDesktopCommand(command) && command !== "help") openApp(command);
  }

  function submitCommand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    runCommand(input);
  }

  return (
    <main className="windows-desktop-page">
      <section
        ref={desktopRef}
        className="windows-desktop-canvas"
        aria-label="Brian Zeng Windows workstation"
        data-capture-width="1920"
        data-capture-height="1080"
      >
        <nav className="windows-desktop-shortcuts" aria-label="Desktop shortcuts">
          <button className="windows-desktop-shortcut" type="button" aria-label="Recycle Bin">
            <span className="windows-shortcut-icon windows-recycle-icon" aria-hidden="true"><Recycle20Regular /></span>
            <span>Recycle Bin</span>
          </button>

          {DESKTOP_ITEMS.map(({ command, Icon, label }) => (
            <button className="windows-desktop-shortcut" key={command} type="button" onClick={() => openApp(command)}>
              <span className={`windows-shortcut-icon windows-shortcut-${command}`} aria-hidden="true"><Icon /></span>
              <span>{label}</span>
            </button>
          ))}
        </nav>

        {terminalOpen && (
          <section
            className="windows-terminal"
            style={frameStyle(frames.terminal)}
            aria-label="Windows Terminal"
            onPointerDown={() => bringToFront("terminal")}
          >
            <header className="windows-terminal-titlebar" onPointerDown={(event) => beginWindowAction(event, "terminal", "drag")}>
              <div className="windows-terminal-tab"><WindowConsole20Regular aria-hidden="true" /><span>Terminal</span></div>
              <button className="windows-terminal-new-tab" type="button" aria-label="New tab" onPointerDown={(event) => event.stopPropagation()}>+</button>
              <span className="windows-terminal-title">Command Prompt</span>
              <div className="windows-terminal-controls">
                <button type="button" onPointerDown={(event) => event.stopPropagation()} onClick={() => setTerminalOpen(false)} aria-label="Minimize Terminal"><Subtract16Regular /></button>
                <button type="button" onPointerDown={(event) => event.stopPropagation()} onClick={() => maximizeWindow("terminal")} aria-label="Maximize Terminal"><Square16Regular /></button>
                <button className="windows-terminal-close" type="button" onPointerDown={(event) => event.stopPropagation()} onClick={() => setTerminalOpen(false)} aria-label="Close Terminal"><Dismiss16Regular /></button>
              </div>
            </header>

            <div className="windows-terminal-body" role="log" aria-live="polite" onClick={() => inputRef.current?.focus()}>
              <p>Microsoft Windows [Version 11.0.26100.4946]</p>
              <p>(c) Microsoft Corporation. All rights reserved.</p>
              <br />

              {transcript.map((entry, index) => (
                <div className="windows-terminal-entry" key={`${entry.command}-${index}`}>
                  <p>C:\Users\Brian&gt;{entry.command}</p>
                  {entry.lines.map((line) => <p key={line}>{line}</p>)}
                  <br />
                </div>
              ))}

              <form className="windows-terminal-prompt" onSubmit={submitCommand}>
                <label htmlFor="desktop-command">C:\Users\Brian&gt;</label>
                <input
                  id="desktop-command"
                  ref={inputRef}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  autoCapitalize="none"
                  autoComplete="off"
                  autoFocus
                  spellCheck={false}
                  aria-label="Terminal command"
                />
              </form>
            </div>
            <button className="windows-resize-handle" type="button" aria-label="Resize Terminal" onPointerDown={(event) => beginWindowAction(event, "terminal", "resize")} />
          </section>
        )}

        {openApps.help && (
          <AppWindow id="help" title="Help" Icon={QuestionCircle24Regular} frame={frames.help} onBringToFront={bringToFront} onClose={closeApp} onDragStart={(event, id) => beginWindowAction(event, id, "drag")} onMaximize={maximizeWindow} onResizeStart={(event, id) => beginWindowAction(event, id, "resize")}>
            <div className="windows-help-app">
              <h2>Command reference</h2>
              <dl>
                <div><dt>help</dt><dd>Show the available commands.</dd></div>
                <div><dt>github</dt><dd>Open GitHub Pulse.</dd></div>
                <div><dt>about</dt><dd>Open Brian&apos;s profile.</dd></div>
                <div><dt>contact</dt><dd>Open contact information.</dd></div>
                <div><dt>clear</dt><dd>Clear the terminal output.</dd></div>
              </dl>
            </div>
          </AppWindow>
        )}

        {openApps.github && (
          <AppWindow className="windows-github-app" id="github" title="GitHub Pulse" Icon={Code24Regular} frame={frames.github} onBringToFront={bringToFront} onClose={closeApp} onDragStart={(event, id) => beginWindowAction(event, id, "drag")} onMaximize={maximizeWindow} onResizeStart={(event, id) => beginWindowAction(event, id, "resize")}>
            <GitHubPulse />
          </AppWindow>
        )}

        {openApps.about && (
          <AppWindow id="about" title="About Brian" Icon={Person24Regular} frame={frames.about} onBringToFront={bringToFront} onClose={closeApp} onDragStart={(event, id) => beginWindowAction(event, id, "drag")} onMaximize={maximizeWindow} onResizeStart={(event, id) => beginWindowAction(event, id, "resize")}>
            <article className="windows-about-app">
              <p className="windows-app-kicker">ABOUT</p>
              <h2>Brian Zeng</h2>
              <p>I&apos;m a data-minded builder working across analysis, software, and applied AI.</p>
              <dl>
                <div><dt>Based in</dt><dd>Oakland, California</dd></div>
                <div><dt>Education</dt><dd>UC Santa Barbara · B.S. Probability &amp; Statistics with Data Science · 2026</dd></div>
                <div><dt>Focus</dt><dd>Data analysis, data science, and software</dd></div>
              </dl>
            </article>
          </AppWindow>
        )}

        {openApps.contact && (
          <AppWindow id="contact" title="Contact" Icon={Mail24Regular} frame={frames.contact} onBringToFront={bringToFront} onClose={closeApp} onDragStart={(event, id) => beginWindowAction(event, id, "drag")} onMaximize={maximizeWindow} onResizeStart={(event, id) => beginWindowAction(event, id, "resize")}>
            <div className="windows-contact-app">
              <p className="windows-app-kicker">OPEN CHANNELS</p>
              <h2>Contact Brian</h2>
              <dl>
                <div><dt>Email</dt><dd>bzeng0000@gmail.com</dd></div>
                <div><dt>LinkedIn</dt><dd>linkedin.com/in/brianbzeng</dd></div>
                <div><dt>GitHub</dt><dd>github.com/brianbzeng</dd></div>
              </dl>
            </div>
          </AppWindow>
        )}

        <footer className="windows-taskbar">
          <div className="windows-widgets" aria-hidden="true">
            <WeatherPartlyCloudyNight24Regular />
            <span><b>64°F</b><small>Mostly cloudy</small></span>
          </div>

          <nav className="windows-taskbar-apps" aria-label="Taskbar apps">
            <button className="windows-taskbar-button windows-start" type="button" aria-label="Start"><span aria-hidden="true"><i /><i /><i /><i /></span></button>
            <button className="windows-taskbar-button" type="button" aria-label="Search"><Search24Regular /></button>
            <button className="windows-taskbar-button" type="button" aria-label="Task view"><WindowMultiple24Regular /></button>
            <button className="windows-taskbar-button windows-taskbar-explorer" type="button" aria-label="File Explorer"><Folder24Regular /></button>
            <button className="windows-taskbar-button windows-taskbar-edge" type="button" aria-label="Microsoft Edge"><Globe24Regular /></button>
            <button className="windows-taskbar-button windows-taskbar-store" type="button" aria-label="Microsoft Store"><ShoppingBag24Regular /></button>
            <button className={`windows-taskbar-button windows-taskbar-terminal ${terminalOpen ? "is-active" : ""}`} type="button" onClick={openTerminal} aria-label="Terminal"><WindowConsole20Regular /></button>
          </nav>

          <div className="windows-system-tray" aria-label="System tray">
            <ChevronUp12Regular aria-hidden="true" />
            <Wifi420Regular aria-label="Network connected" />
            <Speaker220Regular aria-label="Audio enabled" />
            <span className="windows-taskbar-clock"><b>9:06 PM</b><small>9/3/2026</small></span>
          </div>
        </footer>
      </section>
    </main>
  );
}
