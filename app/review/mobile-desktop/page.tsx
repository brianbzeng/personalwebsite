import type { Metadata } from "next";
import MonitorDesktop from "../../components/MonitorDesktop";

export const metadata: Metadata = {
  title: "Mobile Desktop Review / Brian Zeng",
  robots: { index: false, follow: false },
};

export default function MobileDesktopReview() {
  return <MonitorDesktop mobileLayout />;
}
