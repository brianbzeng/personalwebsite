import type { Metadata } from "next";
import ThemeToggle from "../components/ThemeToggle";

export const metadata: Metadata = {
  title: "Contact — Brian Zeng",
  description: "Email, LinkedIn, and GitHub for Brian Zeng.",
};

const contactLinks = [
  {
    index: "01",
    label: "Email",
    value: "bzeng0000@gmail.com",
    href: "mailto:bzeng0000@gmail.com",
  },
  {
    index: "02",
    label: "LinkedIn",
    value: "linkedin.com/in/brianbzeng",
    href: "https://www.linkedin.com/in/brianbzeng",
  },
  {
    index: "03",
    label: "GitHub",
    value: "github.com/brianbzeng",
    href: "https://github.com/brianbzeng",
  },
];

export default function ContactPage() {
  return (
    <main id="top" className="contact-page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="Brian Zeng, home">
          <span>BZ</span>
          <span className="brand-index">/ 01</span>
        </a>
        <nav aria-label="Primary navigation">
          <a className="nav-skills" href="/#skills">Skills</a>
          <a className="nav-projects" href="/#work">Projects</a>
          <a className="nav-f1" href="/#f1-lab">F1 Demo</a>
          <a className="nav-contact" href="/contact" aria-current="page">Contact</a>
        </nav>
        <div className="header-actions">
          <ThemeToggle />
          <a
            className="header-github"
            href="https://github.com/brianbzeng"
            target="_blank"
            rel="noreferrer"
          >
            GitHub <span aria-hidden="true">↗</span>
          </a>
        </div>
      </header>

      <section className="contact-hero shell" aria-labelledby="contact-title">
        <div className="contact-heading">
          <p className="kicker">Contact / 2026</p>
          <h1 id="contact-title">Contact</h1>
        </div>

        <div className="contact-list">
          {contactLinks.map((link) => (
            <a
              className="contact-row"
              href={link.href}
              key={link.label}
              target={link.href.startsWith("http") ? "_blank" : undefined}
              rel={link.href.startsWith("http") ? "noreferrer" : undefined}
            >
              <span className="contact-index">{link.index}</span>
              <span className="contact-label">{link.label}</span>
              <strong>{link.value}</strong>
              <span className="contact-arrow" aria-hidden="true">↗</span>
            </a>
          ))}
        </div>
      </section>

      <footer className="contact-footer shell">
        <p>Brian Zeng · Oakland, California</p>
        <a href="/">Back home ←</a>
      </footer>
    </main>
  );
}
