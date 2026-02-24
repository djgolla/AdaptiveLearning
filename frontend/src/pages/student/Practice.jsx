export default function Practice() {
  return (
    <main className="max-w-5xl mx-auto px-4 py-12">
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="bg-blue-600 p-8 text-white">
          <h1 className="text-3xl font-bold mb-2">Practice Mode</h1>
          <p className="text-blue-100">Get ready for adaptive learning</p>
        </div>

        {/* Content */}
        <div className="p-12 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Questions Coming Soon</h2>
          <p className="text-gray-600 text-lg mb-8 max-w-2xl mx-auto">
            We're preparing an adaptive question set tailored for your learning journey. 
            The system will analyze your responses and adjust difficulty in real-time.
          </p>

          {/* Info Grid */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-8">
            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-2">Smart Difficulty</h3>
              <p className="text-sm text-gray-600">Questions adapt to your skill level automatically</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-2">Multiple Subjects</h3>
              <p className="text-sm text-gray-600">Math, science, and more coming soon</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-2">Real Progress</h3>
              <p className="text-sm text-gray-600">Track your improvement over time</p>
            </div>
          </div>

          {/* Developer Note */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-left max-w-3xl mx-auto">
            <p className="font-semibold text-blue-900 mb-2">For Developers</p>
            <p className="text-sm text-blue-700">
              Question data will be loaded from Supabase here. The adaptive system will select 
              questions based on user performance, cognitive state from the Muse headband, and 
              emotional indicators from facial recognition.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}