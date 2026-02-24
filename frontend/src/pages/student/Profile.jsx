import { useAuth } from '../../context/AuthContext'

export default function Profile() {
  const { user } = useAuth()

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Your Profile</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User Card */}
        <div className="lg:col-span-1">
          <div className="bg-blue-600 rounded-xl shadow-lg p-8 text-white text-center">
            <div className="w-24 h-24 bg-blue-700 rounded-full flex items-center justify-center text-4xl mb-4 mx-auto">
              {user?.email?.[0]?.toUpperCase() || 'S'}
            </div>
            <h2 className="text-2xl font-bold mb-2">Student</h2>
            <p className="text-blue-100 text-sm break-all mb-6">{user?.email}</p>
            
            <div className="bg-blue-700 rounded-lg p-4">
              <p className="text-sm text-blue-200 mb-1">Member Since</p>
              <p className="text-lg font-semibold">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Today'}
              </p>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Learning Preferences */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Learning Preferences</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulty Preference
                </label>
                <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option>Adaptive (Recommended)</option>
                  <option>Easy</option>
                  <option>Medium</option>
                  <option>Hard</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Session Duration
                </label>
                <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option>15 minutes</option>
                  <option>30 minutes</option>
                  <option>45 minutes</option>
                  <option>60 minutes</option>
                </select>
              </div>
            </div>
          </div>

          {/* Device Integrations */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Device Integrations</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div>
                  <p className="font-semibold text-gray-900">Muse Headband</p>
                  <p className="text-sm text-gray-600">Monitor cognitive signals</p>
                </div>
                <button className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition">
                  Connect
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div>
                  <p className="font-semibold text-gray-900">Webcam Monitoring</p>
                  <p className="text-sm text-gray-600">Track facial emotions</p>
                </div>
                <button className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition">
                  Enable
                </button>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Your Statistics</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-6 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-3xl font-bold text-blue-600 mb-1">0</p>
                <p className="text-sm text-gray-600 font-medium">Total Sessions</p>
              </div>

              <div className="text-center p-6 bg-green-50 rounded-lg border border-green-200">
                <p className="text-3xl font-bold text-green-600 mb-1">0</p>
                <p className="text-sm text-gray-600 font-medium">Questions Mastered</p>
              </div>

              <div className="text-center p-6 bg-orange-50 rounded-lg border border-orange-200">
                <p className="text-3xl font-bold text-orange-600 mb-1">0h</p>
                <p className="text-sm text-gray-600 font-medium">Total Time</p>
              </div>

              <div className="text-center p-6 bg-purple-50 rounded-lg border border-purple-200">
                <p className="text-3xl font-bold text-purple-600 mb-1">0</p>
                <p className="text-sm text-gray-600 font-medium">Achievements</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}