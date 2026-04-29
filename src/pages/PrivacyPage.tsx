export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
      
      <div className="space-y-8 text-slate-600 dark:text-slate-400 leading-relaxed">
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">What data is collected</h2>
          <p>
            When you use AIATS, we collect information necessary to analyze your career profile and matching against job descriptions. This includes your resume text, public profile data from platforms you choose to link (GitHub, LeetCode, Codeforces), and target job descriptions.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Resume Processing</h2>
          <p>
            Resumes uploaded are processed in-memory to extract necessary text features to feed our models. We do not store raw resumes permanently without your explicit consent. Extracted keywords are stored anonymously to build global models.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Public Platform Data</h2>
          <p>
            By providing your GitHub, LeetCode, or Codeforces usernames, you authorize us to fetch public data through their respective public APIs. 
          </p>
        </section>
      </div>
    </div>
  );
}
