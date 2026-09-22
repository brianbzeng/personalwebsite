import { Fragment, type ReactNode } from "react";
import type { BoardNote, NoteText } from "./notesData";
import { safeNoteSrc } from "./noteEditor";

function FormattedText({ content }: { content: NoteText[] }) {
  return content.map((part, index) => {
    let text: ReactNode = part.text;
    if (part.marks?.includes("bold")) text = <strong>{text}</strong>;
    if (part.marks?.includes("italic")) text = <em>{text}</em>;
    if (part.marks?.includes("underline")) text = <span className="note-underline">{text}</span>;
    if (part.marks?.includes("strikethrough")) text = <s>{text}</s>;
    return <Fragment key={index}>{text}</Fragment>;
  });
}

/** Matches the editor's Mac-style check: rounded stroke, centered inside the bubble. */
function CheckMark() {
  return <svg viewBox="0 0 12 10" fill="none" aria-hidden="true" focusable="false">
    <path d="M2 5.4 4.8 8 10 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>;
}

export default function NoteContent({ note, preview = false }: { note: BoardNote; preview?: boolean }) {
  return <div className={`note-content${preview ? " is-preview" : ""}`}>
    {(preview ? note.blocks.slice(0, 2) : note.blocks).map((block, index) => {
      if (block.type === "checklist") return <ul className="note-checklist" key={index}>{block.items.map((item, itemIndex) => <li key={itemIndex} className={item.checked ? "is-checked" : ""}>
        <span className="note-check" role="img" aria-label={item.checked ? "Completed" : "Not completed"}>{item.checked ? <CheckMark /> : null}</span>
        <span><FormattedText content={item.content} /></span>
      </li>)}</ul>;
      if (block.type === "bullets" || block.type === "numbered") {
        const List = block.type === "numbered" ? "ol" : "ul";
        return <List key={index}>{block.items.map((item, itemIndex) => <li key={itemIndex}><FormattedText content={item} /></li>)}</List>;
      }
      if (block.type === "table") return <div className="note-table-wrap" key={index} role="group" aria-label="Table">
        <table className="note-table"><tbody>{block.rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>)}</tbody></table>
      </div>;
      if (block.type === "image") {
        const src = safeNoteSrc(block.src);
        if (!src) return null;
        // eslint-disable-next-line @next/next/no-img-element
        return <img className="note-image" key={index} src={src} alt={block.alt ?? ""} loading="lazy" />;
      }
      if (block.type === "attachment") {
        const src = safeNoteSrc(block.src);
        if (!src) return null;
        return <a className="note-attachment" key={index} href={src} download={block.name}>📎 {block.name}</a>;
      }
      const Tag = block.type === "heading" ? "h2" : block.type === "subheading" ? "h3" : "p";
      return <Tag key={index}><FormattedText content={block.content} /></Tag>;
    })}
  </div>;
}
