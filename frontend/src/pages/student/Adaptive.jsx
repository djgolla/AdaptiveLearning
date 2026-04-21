import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { supabase } from '../../lib/supabase'

const TOPICS = ['ordering','rationals','expressions','algebra','geometry','angle_relationships','mean','median','mode','probability']
const ICONS  = { ordering:'🔢', rationals:'➗', expressions:'📐', algebra:'🔣', geometry:'📏', angle_relationships:'📐', mean:'〰️', median:'📊', mode:'🔁', probability:'🎲' }
const SHORT  = { angle_relationships: 'Angle Rel.' }

const initSubjects = () => {
  const s = {}
  TOPICS.forEach(t => { s[t] = { correct: 0, attempts: 0 } })
  return s
}

export default function Adaptive() {
  const { user } = useAuth()

  const [accuracyStats, setAccuracyStats] = useState(() => {
    const saved = localStorage.getItem('accuracyStats')
    if (saved) return JSON.parse(saved)
    return { total: { correct: 0, attempts: 0 }, subjects: initSubjects() }
  })

  const [data, setData]             = useState(null)
  const [phase, setPhase]           = useState('idle') // idle | loading | question | result
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [activeButton, setActiveButton]     = useState(null)
  const [correct, setCorrect]       = useState(false)
  const [sessionCount, setSessionCount] = useState(0)
  const [error, setError]           = useState(false)

  useEffect(() => {
    localStorage.setItem('accuracyStats', JSON.stringify(accuracyStats))
  }, [accuracyStats])

  const sendAccuracyToBackend = async () => {
    const { data: topicRows, error: topicError } = await supabase.from('math_topics').select('id, topic_name')
    if (topicError) { console.error(topicError); return }

    const topicMap = {}
    topicRows.forEach(t => { topicMap[t.topic_name] = t.id })

    const rows = Object.entries(accuracyStats.subjects).map(([name, vals]) => ({
      user_id: user.id,
      topic_id: topicMap[name],
      correct_questions: Number(vals.correct) || null,
      attempted_questions: Number(vals.attempts) || null,
    }))

    const { error } = await supabase.from('user_math_performance').upsert(rows, { onConflict: 'user_id,topic_id' })
    if (error) console.error(error)
  }

  const fetchQuestion = async () => {
    setPhase('loading')
    setError(false)
    try {
      await sendAccuracyToBackend()
      // const res  = await fetch(`http://localhost:5000/?user_id=${user.id}`)
      const res = await fetch(`http://localhost:8000/api/generate-question?user_id=${user.id}`, {
        method: 'GET', 
        headers: {//NOT SURE IF NEEDED
          'Authorization': `Bearer ${user.access_token}`
        }
      })
      const json = await res.json()
      if (!json?.question_text) throw new Error('Invalid response')
      setData(json)
      setActiveButton(null)
      setSelectedAnswer(null)
      setPhase('question')
    } catch (err) {
      console.error(err)
      setError(true)
      setPhase('idle')
    }
  }

  const handleSubmit = () => {
    const isCorrect = JSON.stringify(data.answer_options[selectedAnswer]) === JSON.stringify(data.correct_answer)
    setCorrect(isCorrect)
    setSessionCount(n => n + 1)
    setAccuracyStats(prev => {
      const n    = JSON.parse(JSON.stringify(prev))
      const topic = data.question_topic
      n.total.attempts += 1
      if (n.subjects[topic]) n.subjects[topic].attempts += 1
      if (isCorrect) {
        n.total.correct += 1
        if (n.subjects[topic]) n.subjects[topic].correct += 1
      }
      return n
    })
    setPhase('result')
  }

  const getAcc = (topic) => {
    const s = accuracyStats.subjects[topic]
    if (!s || s.attempts === 0) return null
    return Math.round((s.correct / s.attempts) * 100)
  }

  const totalAcc = accuracyStats.total.attempts > 0
    ? Math.round((accuracyStats.total.correct / accuracyStats.total.attempts) * 100)
    : null

  return (
    <div className="p-6 lg:p-8 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h1 className="text-3xl font-black text-gray-900 dark:text-white">🧠 AI Adaptive Practice</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">The AI picks your weakest topic and generates a custom question.</p>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* question panel */}
        <div className="lg:col-span-2 space-y-4">
          {/* session stats bar */}
          {sessionCount > 0 && (
            <div className="flex gap-3 flex-wrap">
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 px-4 py-2 flex items-center gap-2 shadow-sm">
                <span className="text-sm font-bold text-gray-700 dark:text-gray-300">📝 {sessionCount} answered</span>
              </div>
              {totalAcc !== null && (
                <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 px-4 py-2 flex items-center gap-2 shadow-sm">
                  <span className={`text-sm font-bold ${totalAcc >= 70 ? 'text-green-600' : totalAcc >= 40 ? 'text-amber-600' : 'text-rose-600'}`}>
                    🎯 {totalAcc}% accuracy
                  </span>
                </div>
              )}
            </div>
          )}

          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm overflow-hidden">
            {/* idle */}
            {phase === 'idle' && (
              <div className="p-10 text-center">
                <motion.div animate={{ y: [0, -8, 0] }} transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                  className="text-6xl mb-4">🚀</motion.div>
                <h2 className="text-xl font-black text-gray-900 dark:text-white mb-2">Ready to practice?</h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm mb-6 max-w-sm mx-auto">
                  The AI analyses your performance across 10 topics and picks the one you need most.
                </p>
                <motion.button onClick={fetchQuestion}
                  whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                  className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-bold shadow-lg hover:from-indigo-700 hover:to-violet-700 transition">
                  Generate Question
                </motion.button>
                {error && <p className="text-rose-500 text-sm mt-4">⚠️ Generation failed — try again.</p>}
              </div>
            )}

            {/* loading */}
            {phase === 'loading' && (
              <div className="p-10 text-center">
                <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">AI is picking your topic...</p>
              </div>
            )}

            {/* question / result */}
            {(phase === 'question' || phase === 'result') && data && (
              <div className="p-7">
                <div className="flex gap-2 mb-4 flex-wrap">
                  {data.question_topic && (
                    <span className="text-xs font-bold px-2.5 py-1 bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 rounded-full capitalize flex items-center gap-1">
                      {ICONS[data.question_topic]} {data.question_topic.replace('_', ' ')}
                    </span>
                  )}
                  {data.difficulty && (
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full capitalize ${data.difficulty === 'easy' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : data.difficulty === 'hard' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'}`}>
                      {data.difficulty}
                    </span>
                  )}
                </div>

                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-6 leading-relaxed">{data.question_text}</p>

                <div className="space-y-3 mb-6">
                  {data.answer_options?.map((opt, i) => {
                    const isSelected = activeButton === i
                    const isResult   = phase === 'result'
                    const isCorrectOpt = isResult && JSON.stringify(opt) === JSON.stringify(data.correct_answer)
                    const isWrong      = isResult && isSelected && !isCorrectOpt

                    let style = 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:border-indigo-300'
                    if (isResult) {
                      if (isCorrectOpt) style = 'border-green-400 bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                      else if (isWrong)  style = 'border-rose-400 bg-rose-50 dark:bg-rose-900/30 text-rose-800 dark:text-rose-200'
                      else style = 'border-gray-100 dark:border-gray-700 opacity-50'
                    } else if (isSelected) {
                      style = 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-200'
                    }

                    return (
                      <motion.button key={i} onClick={() => { if (phase !== 'question') return; setSelectedAnswer(i); setActiveButton(i) }}
                        disabled={phase === 'result'}
                        whileHover={phase === 'question' ? { x: 4 } : {}}
                        className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-200 flex items-center gap-3 ${style}`}
                      >
                        <span className="w-7 h-7 flex-shrink-0 rounded-lg bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 flex items-center justify-center text-sm font-bold">
                          {String.fromCharCode(65 + i)}
                        </span>
                        <span>{Array.isArray(opt) ? opt.join(', ') : opt}</span>
                        {isResult && isCorrectOpt && <span className="ml-auto text-green-500 text-lg">✓</span>}
                        {isResult && isWrong      && <span className="ml-auto text-rose-500 text-lg">✗</span>}
                      </motion.button>
                    )
                  })}
                </div>

                {phase === 'question' && (
                  <button onClick={handleSubmit} disabled={selectedAnswer === null}
                    className="w-full py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:from-indigo-700 hover:to-violet-700 transition shadow">
                    Submit Answer
                  </button>
                )}

                {phase === 'result' && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                    <div className={`p-4 rounded-xl text-center font-black text-lg ${correct ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-rose-50 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300'}`}>
                      {correct ? '🎉 Correct! Great job!' : '❌ Not quite — keep going!'}
                    </div>
                    <motion.button onClick={fetchQuestion}
                      whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
                      className="w-full py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-bold hover:from-indigo-700 hover:to-violet-700 transition shadow">
                      Next Question →
                    </motion.button>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* accuracy sidebar */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 shadow-sm h-fit">
          <h3 className="font-black text-gray-900 dark:text-white mb-4">Topic Accuracy</h3>
          <div className="space-y-3">
            {TOPICS.map(topic => {
              const acc = getAcc(topic)
              const s   = accuracyStats.subjects[topic]
              return (
                <div key={topic}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1">
                      {ICONS[topic]} {SHORT[topic] || topic.replace('_', ' ')}
                    </span>
                    <span className={`text-xs font-black ${acc === null ? 'text-gray-400' : acc >= 70 ? 'text-green-600 dark:text-green-400' : acc >= 40 ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400'}`}>
                      {acc === null ? '—' : `${acc}%`}
                    </span>
                  </div>
                  <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full ${acc === null ? '' : acc >= 70 ? 'bg-green-500' : acc >= 40 ? 'bg-amber-500' : 'bg-rose-500'}`}
                      initial={{ width: 0 }}
                      animate={{ width: acc ? `${acc}%` : '0%' }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                  {s?.attempts > 0 && <p className="text-[10px] text-gray-400 mt-0.5">{s.correct}/{s.attempts} correct</p>}
                </div>
              )
            })}
          </div>

          {sessionCount > 0 && (
            <button
              onClick={() => {
                setAccuracyStats({ total: { correct: 0, attempts: 0 }, subjects: initSubjects() })
                setSessionCount(0)
                localStorage.removeItem('accuracyStats')
              }}
              className="mt-5 w-full text-xs text-gray-400 hover:text-rose-500 transition py-2"
            >
              Reset stats
            </button>
          )}
        </div>
      </div>
    </div>
  )
}