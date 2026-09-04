import type { Metadata } from "next";
import MonitorDesktop from "../components/MonitorDesktop";

export const metadata: Metadata = {
  title: "Monitor Desktop / Brian Zeng",
  description: "Brian Zeng's interactive 1920 by 1080 Windows workstation desktop.",
};

export default function DesktopPage() {
  return <MonitorDesktop />;
}
