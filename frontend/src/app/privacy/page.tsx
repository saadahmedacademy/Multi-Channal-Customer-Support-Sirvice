'use client';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-gray-900">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent mb-6">
            Privacy Policy
          </h1>
          <div className="prose dark:prose-invert max-w-none space-y-4 text-gray-700 dark:text-gray-200">
            <p>
              Your privacy is important to us. This policy outlines how we collect, use, and protect your personal information when you use our AI Support Center.
            </p>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">Information We Collect</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Name and email address when you submit a support request</li>
              <li>Message content and conversation history</li>
              <li>Technical data such as browser type and IP address</li>
            </ul>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">How We Use Your Information</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>To process and respond to your support requests</li>
              <li>To improve our AI-powered support system</li>
              <li>To communicate with you about your requests</li>
            </ul>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">Data Protection</h2>
            <p>
              We implement appropriate security measures to protect your personal information. Your data is stored securely and is only accessible to authorized personnel.
            </p>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mt-6">Contact</h2>
            <p>
              If you have any questions about this privacy policy, please contact us at{' '}
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
