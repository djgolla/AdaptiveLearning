import { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/api'

export default function Practice() {
  const [session, setSession] = useState(null)
  const [questions, setQuestions] = useState([])
  const [index, setIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [finished, setFinished] = useState(false)

  useEffect(() => {
    // create session on mount
    startSession()
    // end session on unload
    return () => {
      if (session) {
        endSession(session.id).catch(() => {})
      }
    }
    // eslint-disable-next-line
  }, [])

  async function startSession() {
    setLoading(true)
    try {
      const s = await apiFetch('/api/sessions/start', { method: 'POST', body: { title: 'Practice Session' } })
      setSession(s)
      const qs = await apiFetch('/api/questions?limit=10')
      setQuestions(qs || [])
      setIndex(0)
    } catch (err) {
      console.error(err)
      alert('Failed to start session: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  async function postAnswer(q, selected_index) {
    if (!session) return
    try {
      await apiFetch(`/api/sessions/${session.id}/answer`, {
        method: 'POST',
        body: { question_id: q.id, selected_index, correct: selected_index === q.correct_index }
      })
    } catch (err) {
      console.error('answer error', err)
    }
  }

  async function endSession(sessionId) {
    try {
      await apiFetch(`/api/sessions/${sessionId}/end`, { method: 'POST' })
      setFinished(true)
    } catch (err) {
      console.error('end session error', err)
    }
  }

  function handleSelect(idx) {
    setSelected(idx)
  }

  async function handleSubmit() {
    const q = questions[index]
    if (!q) return
    await postAnswer(q, selected)
    setSelected(null)
    if (index + 1 >= questions.length) {
      // finish
      if (session) {
        await endSession(session.id)
      }
    } else {
      setIndex(index + 1)
    }
  }

  if (loading) return <div className="p-8 text-center">Loading...</div>
  if (!questions || questions.length === 0) {
    return (
      <main className="max-w-4xl mx-auto p-8">
        <div className="bg-white rounded-xl p-12 shadow text-center">
          <h2 className="text-2xl font-bold mb-4">No Questions Available</h2>
          <p className="text-gray-600">Ask your teammate to generate questions or run the LLM endpoint.</p>
        </div>
      </main>
    )
  }

  const q = questions[index]

  return (
    <main className="max-w-3xl mx-auto p-8">
      <div className="bg-white rounded-xl shadow p-8">
        <div className="mb-6">
          <h3 className="text-sm text-gray-500">Session</h3>
          <h2 className="text-2xl font-bold">{session?.title || 'Practice'}</h2>
          <p className="text-sm text-gray-500 mt-1">{index + 1} / {questions.length}</p>
        </div>

        <div className="mb-6">
          <div className="text-lg font-semibold text-gray-800 mb-3">{q.question_text}</div>
          <div className="grid gap-3">
            {q.options.map((opt, i) => (
              <button
                key={i}
                onClick={() => handleSelect(i)}
                className={`text-left p-4 rounded-lg border transition ${
                  selected === i ? 'bg-blue-50 border-blue-300' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <span className="font-medium mr-3">{String.fromCharCode(65 + i)}.</span>
                <span>{opt}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button
            disabled={selected === null}
            onClick={handleSubmit}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {index + 1 >= questions.length ? 'Finish Session' : 'Next'}
          </button>
        </div>
      </div>

      {finished && (
        <div className="mt-6 text-center">
          <p className="text-gray-700">Session finished — check your dashboard for stats.</p>
        </div>
      )}
    </main>
  )
}