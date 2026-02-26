import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'

export default function LLMTest() {
    const { user } = useAuth()
    /*Goal for now: Ask user to input average accuracy for four subjects: Math, Science, English, History*/
    /*Send to python script, have LLM develop its own question to display.*/

    const [mathAccuracy, setMathAccuracy] = useState('')
    const [scienceAccuracy, setScienceAccuracy] = useState('')
    const [englishAccuracy, setEnglishAccuracy] = useState('')
    const [historyAccuracy, setHistoryAccuracy] = useState('')
  
    const[data, setData] = useState([])

    useEffect(() => { 
        fetch('http://localhost:5000/api/data')
        .then(response => response.json())
        .then(data => setData(data))
        .catch(error => console.error('Error fetching data:', error));
    }, []); 

    const handleSubmit = async (e) => {
      e.preventDefault()

      await supabase.from("user_accuracies").insert({
      user : {user}, 
      math_accuracy: mathAccuracy,
      science_accuracy: scienceAccuracy,
      english_accuracy: englishAccuracy,
      history_accuracy: historyAccuracy
    })
    }
  
    return (
     <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">LLM Question Generation</h1>
          <p className="text-gray-600 text-lg">Input your average accuracy for each subject to generate a question</p>
        </div>
        
        {/*Form for inputting accuracies */}
        <div className="bg-white rounded-lg shadow-md p-6 max-w-md">
            <form className="space-y-4 max-w-sm" onSubmit = {handleSubmit}>
                <div className="mb-4">
                    <input type="number" placeholder="Math Accuracy : 0%" 
                    value={mathAccuracy}
                    onChange={(e) => setMathAccuracy(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
                <div>
                    <input type="number" placeholder="Science Accuracy : 0%" 
                    value={scienceAccuracy}
                    onChange={(e) => setScienceAccuracy(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
                <div>
                    <input type="number" placeholder="English Accuracy : 0%" 
                    value={englishAccuracy}
                    onChange={(e) => setEnglishAccuracy(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
                <div>
                    <input type="number" placeholder="History Accuracy : 0%" 
                    value={historyAccuracy}
                    onChange={(e) => setHistoryAccuracy(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
            </form>
            <button type="submit" className="mt-4 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg">
                Generate Question
            </button>
        </div>
        
        {/*Initially display form data as test. End result will be displaying LLM generated question and answer options*/}
        <div className="mt-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Database data:</h2>
            <p className="text-gray-700 text-lg">{data.map((item, index) => 
                <div key={index}>{JSON.stringify(item)}</div>)}</p>
        </div>

     </main>
  )
}