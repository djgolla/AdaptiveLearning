import { Link } from 'react-router-dom'

export default function Dashboard() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Welcome back</h1>
        <p className="text-gray-600 text-lg">Track your progress and continue learning</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all">
          <p className="text-sm font-medium text-gray-600 mb-2">Questions Answered</p>
          <p className="text-4xl font-bold text-gray-900 mb-1">0</p>
          <p className="text-xs text-gray-500">All time</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all">
          <p className="text-sm font-medium text-gray-600 mb-2">Accuracy Rate</p>
          <p className="text-4xl font-bold text-green-600 mb-1">0%</p>
          <p className="text-xs text-gray-500">Average score</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all">
          <p className="text-sm font-medium text-gray-600 mb-2">Current Streak</p>
          <p className="text-4xl font-bold text-orange-600 mb-1">0</p>
          <p className="text-xs text-gray-500">Days in a row</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all">
          <p className="text-sm font-medium text-gray-600 mb-2">Time Spent</p>
          <p className="text-4xl font-bold text-blue-600 mb-1">0h</p>
          <p className="text-xs text-gray-500">This week</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Start Practice Card */}
        <div className="lg:col-span-2">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg p-8 text-white">
            <h2 className="text-3xl font-bold mb-3">Start Practice Session</h2>
            <p className="text-blue-100 mb-6 text-lg">
              Continue where you left off with adaptive questions tailored to your learning style
            </p>
            
            <Link
              to="/practice"
              className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-all"
            >
              Start Practicing
            </Link>

            <div className="flex gap-8 mt-8 pt-6 border-t border-blue-500">
              <div>
                <p className="text-blue-200 text-sm mb-1">Today's Goal</p>
                <p className="text-2xl font-bold">0/10</p>
              </div>
              <div>
                <p className="text-blue-200 text-sm mb-1">Best Streak</p>
                <p className="text-2xl font-bold">0 days</p>
              </div>
            </div>
          </div>
        </div>

        {/* Info Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">How it works</h2>
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Muse Headband Integration</h3>
              <p className="text-sm text-gray-600">Monitors cognitive signals and stress levels in real-time</p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Facial Recognition</h3>
              <p className="text-sm text-gray-600">Tracks emotional responses for better learning insights</p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Adaptive Difficulty</h3>
              <p className="text-sm text-gray-600">System adjusts question difficulty based on your current state</p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-gray-700">
              <strong>Tip:</strong> Practice during your peak focus hours for best results
            </p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Recent Activity</h2>
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-2">No activity yet</p>
          <p className="text-gray-400 text-sm">Start practicing to see your progress here</p>
        </div>
      </div>
    </main>
  )
}