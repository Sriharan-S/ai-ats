import * as React from "react";
import { useState, useRef, FormEvent } from "react";
import { requestJson } from "../api/client";
import { AtsAnalysisResponse } from "../api/types";
import { Button } from "../components/common/Button";
import { TextInput } from "../components/common/TextInput";
import { TextArea } from "../components/common/TextArea";
import { Card, CardHeader, CardTitle, CardContent } from "../components/common/Card";
import { Upload, FileText, Briefcase, ChevronRight, CheckCircle2, TrendingUp, TrendingDown, Target, ExternalLink, ShieldAlert, Activity } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart as ReBarChart, Bar as ReBar, XAxis, YAxis, Tooltip } from "recharts";

export default function AtsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [github, setGithub] = useState("");
  const [leetcode, setLeetcode] = useState("");
  const [codeforces, setCodeforces] = useState("");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AtsAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("explanation");

  const filterInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || !jobDescription) {
      setError("Resume and Job Description are required.");
      return;
    }
    
    setError(null);
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append("resume", file);
      formData.append("job_description", jobDescription);
      formData.append("github", github);
      formData.append("leetcode", leetcode);
      formData.append("codeforces", codeforces);

      const res = await fetch("/api/ats-analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Analysis failed");
      
      setResult(data);
      setActiveTab("explanation");
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setJobDescription("");
    setGithub("");
    setLeetcode("");
    setCodeforces("");
    setResult(null);
    setError(null);
    if (filterInputRef.current) filterInputRef.current.value = '';
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "#10B981"; // Emerald 500
    if (score >= 60) return "#6366f1"; // Indigo 500
    if (score >= 40) return "#f59e0b"; // Amber 500
    return "#f43f5e"; // Rose 500
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">ATS Assessment</h1>
        <p className="text-slate-500 dark:text-slate-400">Analyze your resume against a job description using Explainable AI.</p>
      </div>

      {!result && !loading && (
        <Card className="shadow-sm border-slate-200 dark:border-slate-800">
          <CardContent className="p-6">
            <form onSubmit={handleAnalyze} className="space-y-6">
              
              {error && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm flex items-start gap-2">
                  <ShieldAlert size={18} className="mt-0.5 shrink-0" />
                  <div>{error}</div>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium leading-none">Resume (PDF or DOCX)*</label>
                <div className="flex items-center justify-center w-full">
                  <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 dark:border-slate-700 border-dashed rounded-lg cursor-pointer bg-slate-50 dark:bg-slate-950 hover:bg-slate-100 dark:bg-slate-800">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 mb-2 text-slate-500 dark:text-slate-400" />
                      <p className="mb-1 text-sm text-slate-500 dark:text-slate-400 font-medium">Click to upload or drag and drop</p>
                      <p className="text-xs text-slate-400">PDF or DOCX (MAX. 5MB)</p>
                      {file && <p className="mt-2 text-sm text-slate-900 dark:text-white font-bold">{file.name}</p>}
                    </div>
                    <input id="dropzone-file" type="file" className="hidden" accept=".pdf,.doc,.docx" onChange={handleFileChange} ref={filterInputRef} />
                  </label>
                </div>
              </div>

              <TextArea 
                label="Job Description*" 
                placeholder="Paste the target job description here..." 
                value={jobDescription}
                onChange={e => setJobDescription(e.target.value)}
                className="h-48"
              />

              <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-4">
                <h4 className="text-sm font-medium">Platform Evidence (Optional)</h4>
                <div className="grid sm:grid-cols-3 gap-4">
                  <TextInput placeholder="GitHub Username" value={github} onChange={e => setGithub(e.target.value)} />
                  <TextInput placeholder="LeetCode Username" value={leetcode} onChange={e => setLeetcode(e.target.value)} />
                  <TextInput placeholder="Codeforces Handle" value={codeforces} onChange={e => setCodeforces(e.target.value)} />
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" size="lg" className="w-full sm:w-auto">
                  <Activity size={18} className="mr-2" /> Analyze Resume
                </Button>
                <Button type="button" variant="outline" size="lg" onClick={handleClear} className="w-full sm:w-auto">
                  Clear
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card className="shadow-sm border-slate-200 dark:border-slate-800 p-12 text-center">
          <div className="w-16 h-16 border-4 border-slate-200 dark:border-slate-800 border-t-slate-800 rounded-full animate-spin mx-auto mb-6"></div>
          <h3 className="text-xl font-bold mb-2">Analyzing Profile...</h3>
          <p className="text-slate-500 dark:text-slate-400">Extracting features, fetching platform evidence, and running the ML pipeline.</p>
        </Card>
      )}

      {result && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          <Card className="overflow-hidden border-slate-200 dark:border-slate-800">
            <CardContent className="p-0 flex flex-col md:flex-row">
              <div className="bg-slate-900 text-white p-8 md:w-1/3 flex flex-col items-center justify-center text-center">
                <div className="relative w-32 h-32 mb-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[{ value: result.score }, { value: 100 - result.score }]}
                        cx="50%" cy="50%" innerRadius={50} outerRadius={64}
                        startAngle={90} endAngle={-270}
                        dataKey="value" stroke="none"
                        isAnimationActive={true}
                      >
                        <Cell fill={getScoreColor(result.score)} />
                        <Cell fill="rgba(255,255,255,0.1)" />
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <span className="text-4xl font-bold leading-none">{result.score}</span>
                  </div>
                </div>
                <h2 className="text-xl font-bold mb-1">
                  {result.score >= 80 ? 'Strong Match' : result.score >= 60 ? 'Good Match' : result.score >= 40 ? 'Moderate Match' : 'Low Match'}
                </h2>
              </div>
              <div className="p-8 md:w-2/3 flex flex-col justify-center">
                <h3 className="text-lg font-bold mb-2">Executive Summary</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-6 leading-relaxed">
                  {result.recommendations.summary}
                </p>
                <div className="flex flex-wrap gap-2 mb-6">
                  {result.missing_keywords.slice(0, 5).map(kw => (
                    <span key={kw} className="px-2.5 py-1 bg-rose-50 text-rose-700 text-xs font-semibold rounded border border-rose-100">
                      Missing: {kw}
                    </span>
                  ))}
                </div>
                <div className="flex gap-3">
                  <Button onClick={handleClear} variant="outline" size="sm">Assess Another</Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-2 border-b border-slate-200 dark:border-slate-800 pb-px">
            {['explanation', 'gaps', 'platforms'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
                  activeTab === tab 
                    ? 'border-slate-900 text-slate-900 dark:text-white' 
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:border-slate-700'
                }`}
              >
                {tab === 'gaps' ? 'Skill Gaps & Actions' : tab === 'platforms' ? 'Platform Evidence' : 'SHAP Explanation'}
              </button>
            ))}
          </div>

          <div className="min-h-[400px]">
            {activeTab === 'explanation' && (
              <div className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-emerald-600"><TrendingUp className="mr-2" size={20}/> Top Positive Factors</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {result.top_positive.map(([feature, impact]) => (
                        <div key={feature}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-slate-700 dark:text-slate-300 capitalize">{feature.replace(/_/g, ' ')}</span>
                            <span className="text-emerald-600 font-bold">+{impact.toFixed(1)}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                            <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${Math.min(100, Math.abs(impact) * 5)}%` }}></div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-rose-600"><TrendingDown className="mr-2" size={20}/> Top Negative Factors</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {result.top_negative.map(([feature, impact]) => (
                        <div key={feature}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-slate-700 dark:text-slate-300 capitalize">{feature.replace(/_/g, ' ')}</span>
                            <span className="text-rose-600 font-bold">{impact.toFixed(1)}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 flex justify-end">
                            <div className="bg-rose-500 h-2 rounded-full" style={{ width: `${Math.min(100, Math.abs(impact) * 5)}%` }}></div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </div>
                
                <Card>
                  <CardHeader>
                    <CardTitle>Feature Impact (SHAP Values)</CardTitle>
                  </CardHeader>
                  <CardContent className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ReBarChart
                        layout="vertical"
                        data={Object.entries(result.shap_values as Record<string, number>)
                          .map(([name, value]) => ({ name: name.replace(/_/g, ' '), value }))
                          .sort((a,b) => Math.abs(b.value) - Math.abs(a.value))}
                        margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
                      >
                        <XAxis type="number" />
                        <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 12 }} />
                        <Tooltip cursor={{fill: '#f5f5f5'}} />
                        <ReBar dataKey="value" isAnimationActive={false}>
                          {Object.entries(result.shap_values as Record<string, number>).sort((a,b) => Math.abs(b[1]) - Math.abs(a[1])).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry[1] > 0 ? '#10B981' : '#f43f5e'} />
                          ))}
                        </ReBar>
                      </ReBarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'gaps' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-bold">Actionable Missing Skills</h3>
                  <span className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-sm font-medium rounded-full">{result.recommendations.total_gaps} items detailed</span>
                </div>
                
                <div className="grid gap-4">
                  {result.recommendations.gaps.map((gap, i) => (
                    <Card key={i} className="border-l-4 border-l-amber-500">
                      <CardContent className="p-5">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                          <div className="flex items-center gap-3">
                            <h4 className="font-bold text-lg">{gap.skill}</h4>
                            <span className="text-xs px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-400">{gap.topic}</span>
                          </div>
                          {gap.roadmap_available && (
                            <Button variant="outline" size="sm" onClick={() => window.open(gap.roadmap_url || '#', '_blank')}>
                              View Roadmap <ExternalLink size={14} className="ml-2"/>
                            </Button>
                          )}
                        </div>
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Advice</p>
                            <p className="text-slate-800 dark:text-slate-200">{gap.advice}</p>
                          </div>
                          <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded border border-slate-100 dark:border-slate-800">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Action items</p>
                            <p className="text-slate-800 dark:text-slate-200 text-sm">{gap.action}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'platforms' && (
              <div className="grid md:grid-cols-3 gap-6">
                <Card>
                  <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                    <CardTitle className="flex items-center gap-2"><Activity size={18}/> GitHub Data</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    {result.platform_data.github.total_commits ? (
                      <>
                        <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Commits</span><span className="font-bold">{result.platform_data.github.total_commits}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Repos</span><span className="font-bold">{result.platform_data.github.total_repos}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Languages</span><span className="font-bold text-right">{result.platform_data.github.languages.slice(0,3).join(', ')}</span></div>
                      </>
                    ) : (
                      <p className="text-slate-500 dark:text-slate-400 italic">No data provided or fetched.</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                    <CardTitle className="flex items-center gap-2"><Target size={18}/> LeetCode Data</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    {result.platform_data.leetcode.solved ? (
                      <>
                        <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Solved</span><span className="font-bold">{result.platform_data.leetcode.solved}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Ranking</span><span className="font-bold">{result.platform_data.leetcode.ranking.toLocaleString()}</span></div>
                      </>
                    ) : (
                      <p className="text-slate-500 dark:text-slate-400 italic">No data provided or fetched.</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                    <CardTitle className="flex items-center gap-2"><Target size={18}/> Codeforces Data</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    {result.platform_data.codeforces.rating ? (
                      <>
                        <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Rating</span><span className="font-bold">{result.platform_data.codeforces.rating}</span></div>
                      </>
                    ) : (
                      <p className="text-slate-500 dark:text-slate-400 italic">No data provided or fetched.</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
