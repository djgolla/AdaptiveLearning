import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { supabase } from '../../lib/supabase'

//Test sending information back and forth between front/backend and submitting data to LLM
//Possibly update in future where accuracy values update automatically depending on success. 
//LLM does occasionally fail to give a correct solution to answer. 

export default function LLMTest() {
    const { user } = useAuth()

    const [showGeneratedQuestion, setShowGeneratedQuestion] = useState(false)
    const [activeButton, setActiveButton] = useState(null)
    const [selectedAnswer, setSelectedAnswer] = useState(null)
    const [submitted, setSubmitted] = useState(false)
    const [correct, setCorrect] = useState(false)

    const topicList = [
        "ordering",
        "rationals",
        "operations",
        "expressions",
        "algebra",
        "geometry",
        "angle_relationships",
        "mean",
        "median",
        "mode",
        "probability"
    ]

    const [topics, setTopics] = useState(() => {
        const initial = {}

        topicList.forEach(topic => {
            initial[topic] = {
                accuracy: "",
                stress: ""
            }
        })

        return initial
    })

    const [data, setData] = useState(null)

    useEffect(() => {
        if (!user) return

        fetch(`http://localhost:5000/api/performance?user_id=${user.id}`)
            .then(response => response.json())
            .then(data => setData(data))
            .catch(error => console.error('Error fetching data:', error))
    }, [user])

    const handleChange = (topic, field, value) => {
        setTopics(prev => ({
            ...prev,
            [topic]: {
                ...prev[topic],
                [field]: value
            }
        }))
    }

    const handleAnswerSelect = (index) => {
        setSelectedAnswer(index)
        setActiveButton(index)
    }

    const submitAnswer = () => {
        if(data.answer_options[selectedAnswer].correct == true)
        {
            setCorrect(true)
        } else{
            setCorrect(false)
        }
        setSubmitted(true)
    }




    const handleSubmit = async (e) => {
        e.preventDefault()

        const { data: topicRows, error: topicError } = await supabase
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

        const rows = Object.entries(topics).map(([topicName, values]) => ({
            user_id: user.id,
            topic_id: topicMap[topicName],
            accuracy: Number(values.accuracy) || null,
            stress: Number(values.stress) || null
        }))

        const { error } = await supabase
            .from("user_math_performance")
            .upsert(rows, {
                onConflict: "user_id,topic_id"
            })

        if (error) {
            console.error(error)
        } else {
            console.log("Data saved")
        }

        //not sure if needed
        const response = await fetch("http://localhost:5000/api/performance", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: user.id,
                topics: rows
            })
        })

        const generation = await fetch(`http://localhost:5000/api/generate-question?user_id=${user.id}`)
            .catch(error => console.error('Error fetching data:', error))
        const result = await generation.json()
        setData(result)
        

        // const result = await response.json()
        // setData(result)

        setShowGeneratedQuestion(true)
    }


    return (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    LLM Question Generation (IN PROGRESS)
                </h1>
                <p className="text-gray-600 text-lg">
                    Input your average accuracy and stress values for each topic to generate a question
                </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 max-w-md">

                {!showGeneratedQuestion && (
                    <form onSubmit={handleSubmit} className="space-y-6">

                        {topicList.map(topic => (
                            <div key={topic} className="border p-4 rounder">

                                <h2 className="font-semibold mb-2 capitalize">
                                    {topic.replace("_", " ")}
                                </h2>

                                <div className="flex gap-4">

                                    <input
                                        type="number"
                                        placeholder="Accuracy"
                                        value={topics[topic].accuracy}
                                        onChange={(e) =>
                                            handleChange(topic, "accuracy", e.target.value)
                                        }
                                        className="border p-2 w-full"
                                    />

                                    <input
                                        type="number"
                                        placeholder="Stress"
                                        value={topics[topic].stress}
                                        onChange={(e) =>
                                            handleChange(topic, "stress", e.target.value)
                                        }
                                        className="border p-2 w-full"
                                    />

                                </div>
                            </div>
                        ))}

                        <button 
                            type="submit"
                            className="bg-blue-500 text-white px-6 py-2 rounded"
                        >
                            Generate Question
                        </button>

                    </form>
                )}

                {showGeneratedQuestion && data && (
                    <div className="mt-4">

                        <h2 className="text-lg font-semibold mb-2">
                            Generated Question:
                        </h2>

                        <div className="bg-gray-100 p-4 rounded-lg mb-4">
                            <p className="text-gray-800">{data.question_text}</p>
                        </div>

                        <div>
                            {data.answer_options?.map((option, index) => (
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
                                    {option.value}
                                </button>
                            ))}
                        </div>
                <div>
                <button type="submit" onClick={submitAnswer} className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200">
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

            {submitted && (
            <div>
            <button 
            onClick = {()=> {setSubmitted(false); setShowGeneratedQuestion(false); setSelectedAnswer(null); setActiveButton(null);}}
            className="w-600 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200">
            Next Question! </button>
            </div>
            )}

            </div>

        </main>
    )
}