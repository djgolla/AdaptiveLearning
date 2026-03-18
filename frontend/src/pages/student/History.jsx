import { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/api'

export default function History() {
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    load()
  }, [])

  async function load() {
    try {
      const s = await apiFetch('/api/sessions')
      setSessions(s)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Session History</h1>
      <div className="bg-white rounded-lg shadow p-4">
        {sessions.length === 0 ? (
          <p className="text-gray-500 p-6">No sessions yet</p>
        ) : (
          <table className="w-full">
            <thead className="text-left text-sm text-gray-500">
              <tr>
                <th className="py-2">Started</th>
                <th>Questions</th>
                <th>Correct</th>
                <th>Ended</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <tr key={s.id} className="border-t">
                  <td className="py-3">{new Date(s.started_at).toLocaleString()}</td>
                  <td>{s.questions_answered}</td>
                  <td>{s.correct_answers}</td>
                  <td>{s.ended_at ? new Date(s.ended_at).toLocaleString() : 'In progress'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  )
}