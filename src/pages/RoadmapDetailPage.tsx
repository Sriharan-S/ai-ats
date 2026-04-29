import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, ExternalLink, ChevronDown, ChevronUp, CheckCircle, Circle, PlayCircle, FileText, BookOpen } from "lucide-react";

export default function RoadmapDetailPage() {
  const { slug } = useParams<{slug: string}>();
  const [data, setData] = useState<any>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    fetch(`/api/roadmaps/${slug}`).then(r => r.json()).then((res) => {
      setData(res);
      if (res && res.topics && res.topics.length > 0) {
        setExpanded(res.topics[0].id);
      }
    });
  }, [slug]);

  if (!data) {
    return <div className="p-12 text-center text-slate-500 dark:text-slate-400">Loading roadmap...</div>;
  }

  const getIcon = (type: string) => {
    switch(type) {
      case 'video': return <PlayCircle size={16} />;
      case 'article': return <FileText size={16} />;
      case 'docs': return <BookOpen size={16} />;
      default: return <ExternalLink size={16} />;
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link to="/learn" className="inline-flex items-center text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:text-white mb-6">
        <ArrowLeft size={16} className="mr-2" /> Back to Roadmaps
      </Link>
      
      <div className="mb-10">
        <h1 className="text-4xl font-bold mb-4">{data.title}</h1>
        <p className="text-xl text-slate-600 dark:text-slate-400 leading-relaxed">{data.summary}</p>
      </div>

      <div className="space-y-4">
        {data.topics?.map((topic: any, idx: number) => {
          const isExpanded = expanded === topic.id;
          
          return (
            <div key={topic.id} className="border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 overflow-hidden">
              <button 
                onClick={() => setExpanded(isExpanded ? null : topic.id)}
                className="w-full text-left p-6 flex items-center justify-between hover:bg-slate-50 dark:bg-slate-950 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-sm text-slate-600 dark:text-slate-400">
                    {idx + 1}
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{topic.title}</h3>
                    <div className="flex items-center mt-1">
                      {topic.status === 'completed' ? (
                        <span className="flex items-center text-xs text-emerald-600 font-medium"><CheckCircle size={12} className="mr-1"/> Completed</span>
                      ) : topic.status === 'in-progress' ? (
                        <span className="flex items-center text-xs text-indigo-600 font-medium"><Circle size={12} className="mr-1"/> In Progress</span>
                      ) : (
                        <span className="flex items-center text-xs text-slate-400 font-medium"><Circle size={12} className="mr-1"/> Not Started</span>
                      )}
                    </div>
                  </div>
                </div>
                {isExpanded ? <ChevronUp className="text-slate-400" /> : <ChevronDown className="text-slate-400" />}
              </button>
              
              {isExpanded && (
                <div className="p-6 pt-0 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
                  <p className="text-slate-600 dark:text-slate-400 mb-6 mt-4">{topic.description}</p>
                  
                  <h4 className="font-bold text-sm uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">Resources</h4>
                  <div className="space-y-2">
                    {topic.resources.map((res: any, i: number) => (
                      <a 
                        key={i} 
                        href={res.url} 
                        target="_blank" 
                        rel="noreferrer"
                        className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:border-slate-300 dark:border-slate-700 hover:shadow-sm transition-all group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="text-slate-400 group-hover:text-indigo-500 transition-colors">
                            {getIcon(res.type)}
                          </div>
                          <span className="font-medium text-slate-800 dark:text-slate-200">{res.title}</span>
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded ml-2">
                            {res.type}
                          </span>
                        </div>
                        <ExternalLink size={14} className="text-slate-300 group-hover:text-indigo-500" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
        {(!data.topics || data.topics.length === 0) && (
          <div className="text-center py-12 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 border-dashed rounded-xl">
            <p className="text-slate-500 dark:text-slate-400">No topics available yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
