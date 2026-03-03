import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

//no supabase - just direct contact w/ test3 to see how question generation is working. 
export default function LLMTest2() {
    const { user } = useAuth()
    const[data, setData] = useState([])
    const [showGenerateQuestionButton, setShowGenerateQuestionButton] = useState(true)

    useEffect(() => { //obtain question/answer options from backend. 
        if (!showGenerateQuestionButton) 
        fetch('http://localhost:5000/')
        .then(response => response.json())
        .then(data => setData(data))
        .catch(error => console.error('Error fetching data:', error));
    }, [showGenerateQuestionButton]); //re-run whenever button is clicked to generate new question.


    return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold mb-4">LLM Test 2</h1>
       
        <div className="bg-white rounded-lg shadow-md p-6 max-w-md">
        {showGenerateQuestionButton && (
          <button onClick = {() => setShowGenerateQuestionButton(false)}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200">
          Generate Question </button>
        )}
        {!showGenerateQuestionButton && (
            <div className="mt-4">
                <h2 className="text-lg font-semibold mb-2">Generated Question:</h2>
                <p className="text-gray-700">{JSON.stringify(data, null, 2)}</p>
            </div>
        )}
        </div>

    </main>
)

}
