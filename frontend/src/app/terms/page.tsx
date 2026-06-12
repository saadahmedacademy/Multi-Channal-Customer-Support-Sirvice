'use client';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-gray-900">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent mb-6">
            Terms of Service
          </h1>
          <div className="prose dark:prose-invert max-w-none space-y-4 text-gray-700 dark:text-gray-200">
            <p>
              By using the AI Support Center, you agree to the following terms and conditions.
            </p>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">Use of Service</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>You must provide accurate information when submitting support requests</li>
              <li>You agree not to misuse the service for any unlawful purpose</li>
              <li>We reserve the right to refuse service to anyone</li>
            </ul>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">AI-Generated Responses</h2>
            <p>
              Our AI-powered support system provides automated responses. While we strive for accuracy, AI responses may occasionally contain errors. Critical decisions should be verified with human support.
            </p>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">Limitation of Liability</h2>
            <p>
              We are not liable for any damages arising from the use or inability to use our support service. Our AI responses are provided as-is without any warranty.
            </p>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">Changes to Terms</h2>
            <p>
              We reserve the right to modify these terms at any time. Continued use of the service constitutes acceptance of any changes.
            </p>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">Contact</h2>
            <p>
              For questions about these terms, please contact us at{' '}
              <a href="mailto:lasanitech7@gmail.com" className="text-indigo-600 dark:text-indigo-400 hover:underline">lasanitech7@gmail.com</a>.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-8">
              Last updated: June 2026
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
