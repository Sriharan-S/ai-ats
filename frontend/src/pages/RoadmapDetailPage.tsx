import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen, CheckCircle, ChevronDown, ChevronUp, Circle, ExternalLink, FileText, PlayCircle } from "lucide-react";
import { requestJson } from "../api/client";

interface RoadmapResource {
  title: string;
  url: string;
  type: string;
}

interface RoadmapTopic {
  id: number;
  title: string;
  status: "completed" | "in-progress" | "not-started";
  description: string;
  resources: RoadmapResource[];
}

interface RoadmapDetail {
  slug: string;
  title: string;
  summary: string;
  topics: RoadmapTopic[];
}

function ResourceIcon({ type }: { type: string }) {
  switch (type) {
    case "video":
      return <PlayCircle size={16} />;
    case "article":
      return <FileText size={16} />;
    case "docs":
      return <BookOpen size={16} />;
    default:
      return <ExternalLink size={16} />;
  }
}

export default function RoadmapDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [data, setData] = useState<RoadmapDetail | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) {
      setError("Roadmap not found.");
      return;
    }

    setData(null);
    setError(null);
    requestJson<RoadmapDetail>(`/api/roadmaps/${slug}`)
      .then((res) => {
        setData(res);
        setExpanded(res.topics[0]?.id ?? null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Roadmap could not be loaded.");
      });
  }, [slug]);

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold mb-3">Roadmap not found</h1>
        <p className="text-slate-500 dark:text-slate-400 mb-6">{error}</p>
        <Link to="/learn" className="text-indigo-600 font-medium hover:underline">Back to Roadmaps</Link>
      </div>
    );
  }

  if (!data) {
    return <div className="p-12 text-center text-slate-500 dark:text-slate-400">Loading roadmap...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link to="/learn" className="inline-flex items-center text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white mb-6">
        <ArrowLeft size={16} className="mr-2" /> Back to Roadmaps
      </Link>

      <div className="mb-10">
        <h1 className="text-4xl font-bold mb-4">{data.title}</h1>
        <p className="text-xl text-slate-600 dark:text-slate-400 leading-relaxed">{data.summary}</p>
      </div>

      <div className="space-y-4">
        {data.topics.map((topic, idx) => {
          const isExpanded = expanded === topic.id;

          return (
            <div key={topic.id} className="border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 overflow-hidden">
              <button
                type="button"
                onClick={() => setExpanded(isExpanded ? null : topic.id)}
                className="w-full text-left p-6 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-950 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-sm text-slate-600 dark:text-slate-400">
                    {idx + 1}
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{topic.title}</h3>
                    <div className="flex items-center mt-1">
                      {topic.status === "completed" ? (
                        <span className="flex items-center text-xs text-emerald-600 font-medium"><CheckCircle size={12} className="mr-1" /> Completed</span>
                      ) : topic.status === "in-progress" ? (
                        <span className="flex items-center text-xs text-indigo-600 font-medium"><Circle size={12} className="mr-1" /> In Progress</span>
                      ) : (
                        <span className="flex items-center text-xs text-slate-400 font-medium"><Circle size={12} className="mr-1" /> Not Started</span>
                      )}
                    </div>
                  </div>
                </div>
                {isExpanded ? <ChevronUp className="text-slate-400" /> : <ChevronDown className="text-slate-400" />}
              </button>

              {isExpanded && (
                <div className="p-6 pt-0 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
                  <p className="text-slate-600 dark:text-slate-400 mb-6 mt-4">{topic.description || "No description available yet."}</p>

                  <h4 className="font-bold text-sm uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">Resources</h4>
                  {topic.resources.length > 0 ? (
                    <div className="space-y-2">
                      {topic.resources.map((resource) => (
                        <a
                          key={`${resource.title}-${resource.url}`}
                          href={resource.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-sm transition-all group"
                        >
                          <div className="flex items-center gap-3">
                            <div className="text-slate-400 group-hover:text-indigo-500 transition-colors">
                              <ResourceIcon type={resource.type} />
                            </div>
                            <span className="font-medium text-slate-800 dark:text-slate-200">{resource.title}</span>
                            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded ml-2">
                              {resource.type}
                            </span>
                          </div>
                          <ExternalLink size={14} className="text-slate-300 group-hover:text-indigo-500" />
                        </a>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">No resources available for this topic yet.</p>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {data.topics.length === 0 && (
          <div className="text-center py-12 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 border-dashed rounded-xl">
            <p className="text-slate-500 dark:text-slate-400">No topics available yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
