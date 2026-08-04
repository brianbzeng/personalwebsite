import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ProjectDetail from "../../components/ProjectDetail";
import { getProject, PROJECTS } from "../../data/projects";

export function generateStaticParams() {
  return PROJECTS.map((project) => ({ slug: project.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const project = getProject(slug);
  return {
    title: project ? `${project.title} / Brian Zeng` : "Project / Brian Zeng",
    description: project?.summary ?? "Project case study from Brian Zeng.",
  };
}

export default async function ProjectPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const project = getProject(slug);
  if (!project) notFound();
  return <ProjectDetail project={project} />;
}
