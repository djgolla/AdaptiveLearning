import { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/api'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    loadStats()
  }, [])

  async function loadStats() {
    try {
      const s = await apiFetch('/api/stats/me')
      setStats(s)
    } catch (err) {
      console.error(err)
      setStats({ total_questions: 0, total_correct: 0, current_streak: 0, best_streak: 0 })
    }
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Welcome back</h1>
        <p className="text-gray-600">Track progress and continue learning</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg p-6 shadow">
          <p className="text-sm text-gray-500">Total Questions</p>
          <p className="text-2xl font-bold">{stats?.total_questions ?? 0}</p>
        </div>

        <div className="bg-white rounded-lg p-6 shadow">
          <p className="text-sm text-gray-500">Correct Answers</p>
          <p className="text-2xl font-bold">{stats?.total_correct ?? 0}</p>
        </div>

        <div className="bg-white rounded-lg p-6 shadow">
          <p className="text-sm text-gray-500">Current Streak</p>
          <p className="text-2xl font-bold">{stats?.current_streak ?? 0}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-gradient-to-br from-blue-600 to-blue-700 p-8 rounded-lg text-white">
          <h2 className="text-2xl font-bold mb-2">Start a Practice Session</h2>
          <p className="text-blue-100 mb-4">Jump into adaptive questions.</p>
          <Link to="/practice" className="inline-block bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold">Start Practicing</Link>
        </div>

        <div className="bg-white rounded-lg p-6 shadow">
          <h3 className="font-bold mb-2">Quick Links</h3>
          <ul className="text-sm text-gray-600">
            <li><Link to="/history" className="text-blue-600 hover:underline">Session History</Link></li>
            <li><Link to="/profile" className="text-blue-600 hover:underline">Profile & Preferences</Link></li>
            <li><a href={`${import.meta.env.VITE_API_URL}/api/llm/generate`} className="text-blue-600">(Dev) Generate Questions</a></li>
          </ul>
        </div>
      </div>
    </main>
  )
}