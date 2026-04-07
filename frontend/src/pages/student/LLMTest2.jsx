import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { supabase } from '../../lib/supabase'

export default function LLMTest2() {
    const { user } = useAuth()
    
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
        //POSSIBLY - need to match supabase table, so need correct/attempted rows
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
    
    
    const[data, setData] = useState(null)
    const [error, setError] = useState(false)
    const [showGenerateQuestionButton, setShowGenerateQuestionButton] = useState(true)
    const [activeButton, setActiveButton] = useState(null)
    const [selectedAnswer, setSelectedAnswer] = useState(null)

    const [submitted, setSubmitted] = useState(false)
    const [correct, setCorrect] = useState(false)

    // useEffect(() => { //obtain question/answer options from backend. 
    //     if (!showGenerateQuestionButton) 
    //     sendAccuracyToBackend() //send accuracy for previous question before fetching new one.
    //     fetch('http://localhost:5000/')
    //     .then(response => response.json())
    //     .then(data => {
    //         if (!data || !data.question_text) {
    //             throw new Error("Invalid response")
    //         }
    //         setData(data)
    //     })
    //     .catch(error => {
    //         console.error('Error fetching data:', error);
    //         //alert("Failed to load question. Try again.");
    //         setError(true);
    //         setShowGenerateQuestionButton(true); // allow user to try again
    //     });
    // }, [showGenerateQuestionButton]); //re-run whenever button is clicked to generate new question.

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
        const isCorrect = data.answer_options[selectedAnswer] === data.correct_answer

        setSubmitted(true)
        setCorrect(isCorrect)

        updateStats(isCorrect) 
    }

    //NEED to go back and ensure question_topic is in JSON
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

    //Save stats to local storage so they persist across refreshes.
    //Should modify later to ensure saved to user
    useEffect(() => {
        const saved = localStorage.getItem("accuracyStats");
        if (saved) setAccuracyStats(JSON.parse(saved));
    }, [])

    useEffect(() => {
        localStorage.setItem("accuracyStats", JSON.stringify(accuracyStats));
    }, [accuracyStats])


    const getAccuracy = (topic) => {
        const subjectStats = accuracyStats.subjects[topic]
        if (subjectStats.attempts === 0) return 0
        return (subjectStats.correct / subjectStats.attempts) * 100
    };

    return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold mb-4">LLM Test 2</h1>
       
        <div className="bg-white rounded-lg shadow-md p-6 max-w-md">
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
                
                {/*Answer options. Style should change for whechever button is selected. */}
                <div>
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
                    {option}
                    </button>
                ))}
                </div>

                <div>
                <button type="submit" onClick={handleSubmit} className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200">
                    Submit
                </button>
                </div>
            </div>
        )}
        </div>
        
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

    </main>
)

}
