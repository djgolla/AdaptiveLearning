import { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/api'
import { useAuth } from '../../context/AuthContext'
import { supabase } from '../../lib/supabase'


export default function Practice() {
  const [session, setSession] = useState(null)
  const [questions, setQuestions] = useState([])
  const [index, setIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [finished, setFinished] = useState(false)

//MODIFYING to work with pure LLM generated questions instead of questions stored in supabase. 
//Will need a way to set/track session duration. Ex: end session after 10 questions or 15 mins.
//Should also make first question generation trigger session start/automatically instead of needing to click?

//ISSUES: 
//main.py is currently setup to take openAI key which I do not think we have. 
//Since I am running LLM_topic_decider, I don't think the session setup from main.py will work. 


const { user } = useAuth()
  const[data, setData] = useState(null)
  const [error, setError] = useState(false)
  const [showGenerateQuestionButton, setShowGenerateQuestionButton] = useState(true)
  const [activeButton, setActiveButton] = useState(null)
  const [selectedAnswer, setSelectedAnswer] = useState(null)

  const [submitted, setSubmitted] = useState(false)
  const [correct, setCorrect] = useState(false)
  //send accuracy to backend via supabase. 
  const [accuracyStats, setAccuracyStats] = useState({
        total: {correct: 0, attempts: 0},
        subjects: {
            ordering: {correct: 0, attempts: 0},
            rationals: {correct: 0, attempts: 0},
            expressions: {correct: 0, attempts: 0},
            algebra: {correct: 0, attempts: 0},
            geometry: {correct: 0, attempts: 0},
            angle_relationships: {correct: 0, attempts: 0},
            mean: {correct: 0, attempts: 0},
            median: {correct: 0, attempts: 0},
            mode: {correct: 0, attempts: 0},
            probability: {correct: 0, attempts: 0},
        }
    });

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


  const fetchQuestion = async() => {
        try {
            await sendAccuracyToBackend() //send accuracy for previous question before fetching new one.
            const response = await fetch(`http://localhost:5000/?user_id=${user.id}`)
            const data = await response.json()
            
            if (!data || !data.question_text) {
            throw new Error("Invalid response")
            }
            setData(data)
        } catch (error) {
        console.error(error);
        setError(true);
        setShowGenerateQuestionButton(true);
        }
    }

  async function startSession() {
    setLoading(true)
    try {
      const s = await apiFetch('/api/sessions/start', { method: 'POST', body: { title: 'Practice Session' } })
      setSession(s)
      // const qs = await apiFetch('/api/questions?limit=10')
      // setQuestions(qs || [])
      // setIndex(0)
    } catch (err) {
      console.error(err)
      alert('Failed to start session: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

      
  //sent at start of question generation
  const sendAccuracyToBackend = async(e) => {
      const {data: topicRows, error: topicError} = await supabase
          .from("math_topics")
          .select("id, topic_name")

      if (topicError) {
          console.error(topicError)
          return
      }

      const topicMap = {}

      topicRows.forEach(t => {
          topicMap[t.topic_name] = t.id
        })
      const rows = Object.entries(accuracyStats.subjects).map(([topicName, values]) => ({
          user_id: user.id,
          topic_id: topicMap[topicName],
          correct_questions: Number(values.correct) || null,
          attempted_questions: Number(values.attempts) || null
        }))

      const {error} = await supabase
        .from("user_math_performance")
        .upsert(rows, {
            onConflict: "user_id,topic_id"
        })
        
      if (error) {
            console.error(error)
      } else {
            console.log("Accuracy sent to backend")
        }
    }

  const handleAnswerSelect = (index) => {
        setSelectedAnswer(index)
        setActiveButton(index)
    }

  const resetForNextQuestion = () => {
        setError(false);
        setSubmitted(false);
        setCorrect(false);
        setActiveButton(null);
        setSelectedAnswer(null);
        setData(null);

        setShowGenerateQuestionButton(false); 
        fetchQuestion()
        };

  const handleSubmit = () => {
        const isCorrect = JSON.stringify(data.answer_options[selectedAnswer]) === JSON.stringify(data.correct_answer)
        setSubmitted(true)
        setCorrect(isCorrect)

        updateStats(isCorrect) 
    }

  const updateStats = (correct) => {
        setAccuracyStats(prevStats => {
            const newStats = {...prevStats};
            const topic = data.question_topic

            newStats.total.attempts += 1
            newStats.subjects[topic].attempts += 1

            if (correct) {
                newStats.total.correct += 1
                newStats.subjects[topic].correct += 1
            }

            return newStats
    });
    };

  // async function postAnswer(q, selected_index) {
  //   if (!session) return
  //   try {
  //     await apiFetch(`/api/sessions/${session.id}/answer`, {
  //       method: 'POST',
  //       body: { question_id: q.id, selected_index, correct: selected_index === q.correct_index }
  //     })
  //   } catch (err) {
  //     console.error('answer error', err)
  //   }
  // }

  async function endSession(sessionId) {
    try {
      await apiFetch(`/api/sessions/${sessionId}/end`, { method: 'POST' })
      setFinished(true)
    } catch (err) {
      console.error('end session error', err)
    }
  }

  // function handleSelect(idx) {
  //   setSelected(idx)
  // }

  // async function handleSubmit() {
  //   const q = questions[index]
  //   if (!q) return
  //   await postAnswer(q, selected)
  //   setSelected(null)
  //   if (index + 1 >= questions.length) {
  //     // finish
  //     if (session) {
  //       await endSession(session.id)
  //     }
  //   } else {
  //     setIndex(index + 1)
  //   }
  // }




  if (loading) return <div className="p-8 text-center">Loading...</div>
  // if (!questions || questions.length === 0) {
  //   return (
  //     <main className="max-w-4xl mx-auto p-8">
  //       <div className="bg-white rounded-xl p-12 shadow text-center">
  //         <h2 className="text-2xl font-bold mb-4">No Questions Available</h2>
  //         <p className="text-gray-600">Ask your teammate to generate questions or run the LLM endpoint.</p>
  //       </div>
  //     </main>
  //   )
  // }

  const q = questions[index]

  return (
    <main className="max-w-3xl mx-auto p-8">
      <div className="bg-white rounded-xl shadow p-8">
        <div className="mb-6">
          <h3 className="text-sm text-gray-500">Session</h3>
          <h2 className="text-2xl font-bold">{session?.title || 'Practice'}</h2>
          {/* <p className="text-sm text-gray-500 mt-1">{index + 1} / {questions.length}</p> */}
        </div>
        
        {showGenerateQuestionButton && (
          <button onClick = {resetForNextQuestion}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200">
          Generate Question </button>
        )}

        {!showGenerateQuestionButton && data && ( 
            <div className="mt-4">
                <h2 className="text-lg font-semibold mb-2">Generated Question:</h2>
                <div className="bg-gray-100 p-4 rounded-lg mb-4">
                    <p className="text-gray-800">{data.question_text}</p>
                </div>
        

          <div className="mb-6">
            {/* <div className="text-lg font-semibold text-gray-800 mb-3">{q.question_text}</div> */}
            {/* <div className="grid gap-3"> */}
            {/* {q.options.map((opt, i) => (
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
            ))} */}
            <div className="grid gap-3 mb-6">
            {data.answer_options.map((option, index) => (
                    <button
                    key={index}
                    onClick={() => handleAnswerSelect(index)}
                    style={{
                        backgroundColor: activeButton === index ? "green" : "gray",
                        color: "white",
                        padding: "10px 20px",
                        width: "100%",
                        border: "none",
                        borderRadius: "5px",
                        cursor: "pointer",
                        marginBottom: "10px"
                    }}
                    >
                    {Array.isArray(option) ? option.join(", ") : option}
                    </button>
                ))}
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={selectedAnswer === null}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Submit
          </button>

        </div>
        </div>
      )}


      {submitted && correct && (
            <div>
                <p>Correct!</p>
            </div>
      )}
      {submitted && !correct && (
            <div>
                <p>Incorrect.</p>
            </div>
        )}

      {error && (
            <div className="mt-4 text-red-600">
                <p>Question generation failed. Please try again!</p>
            </div>
        )}

      {submitted && (
            <div>
            <button 
            onClick = {()=> {setShowGenerateQuestionButton(true); setSubmitted(false);}}
            className="w-600 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200">
            Next Question! </button>
            </div>
        )}

        {/* <div className="flex justify-end gap-3">
          <button
            disabled={selected === null}
            onClick={handleSubmit}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {index + 1 >= questions.length ? 'Finish Session' : 'Next'}
          </button>
        </div> */}
      </div>

      {finished && (
        <div className="mt-6 text-center">
          <p className="text-gray-700">Session finished — check your dashboard for stats.</p>
        </div>
      )}
    </main>
  )
}