import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

//no supabase - just direct contact w/ test3 to see how question generation is working. 
export default function LLMTest2() {
    const { user } = useAuth()
    
    const [stats, setStats] = useState({
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
    
    
    
    
    const[data, setData] = useState(null)
    const [error, setError] = useState(false)
    const [showGenerateQuestionButton, setShowGenerateQuestionButton] = useState(true)
    const [activeButton, setActiveButton] = useState(null)
    const [selectedAnswer, setSelectedAnswer] = useState(null)

    const [submitted, setSubmitted] = useState(false)
    const [correct, setCorrect] = useState(false)

    useEffect(() => { //obtain question/answer options from backend. 
        if (!showGenerateQuestionButton) 
        fetch('http://localhost:5000/')
        .then(response => response.json())
        .then(data => {
            if (!data || !data.question_text) {
                throw new Error("Invalid response")
            }
            setData(data)
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            //alert("Failed to load question. Try again.");
            setError(true);
            setShowGenerateQuestionButton(true); // allow user to try again
        });
    }, [showGenerateQuestionButton]); //re-run whenever button is clicked to generate new question.

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

        setShowGenerateQuestionButton(false); // triggers fetch
        };

    const handleSubmit = () => {
        setSubmitted(true)
        
        if (data.answer_options[selectedAnswer] === data.correct_answer) {
        setCorrect(true)
        } else {
            setCorrect(false)
        }

        updateStats(correct)
    }

    //NEED to go back and ensure question_topic is in JSON
    const updateStats = (correct) => {
        setStats(prevStats => {
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
        const saved = localStorage.getItem("stats");
        if (saved) setStats(JSON.parse(saved));
    }, [])

    useEffect(() => {
        localStorage.setItem("stats", JSON.stringify(stats));
    }, [stats])


    const getAccuracy = (topic) => {
        const subjectStats = stats.subjects[topic]
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
