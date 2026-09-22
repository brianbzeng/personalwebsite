import { Fragment, type ReactNode } from "react";
import type { BoardNote, NoteText } from "./notesData";

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

export default function NoteContent({ note, preview = false }: { note: BoardNote; preview?: boolean }) {
  return <div className={`note-content${preview ? " is-preview" : ""}`}>
    {(preview ? note.blocks.slice(0, 2) : note.blocks).map((block, index) => {
      if (block.type === "checklist") return <ul className="note-checklist" key={index}>{block.items.map((item, itemIndex) => <li key={itemIndex} className={item.checked ? "is-checked" : ""}>
        <span className="note-check" role="img" aria-label={item.checked ? "Completed" : "Not completed"}>{item.checked ? "✓" : ""}</span>
        <span><FormattedText content={item.content} /></span>
      </li>)}</ul>;
      if (block.type === "bullets" || block.type === "numbered") {
        const List = block.type === "numbered" ? "ol" : "ul";
        return <List key={index}>{block.items.map((item, itemIndex) => <li key={itemIndex}><FormattedText content={item} /></li>)}</List>;
      }
      const Tag = block.type === "heading" ? "h2" : block.type === "subheading" ? "h3" : "p";
      return <Tag key={index}><FormattedText content={block.content} /></Tag>;
    })}
  </div>;
}
