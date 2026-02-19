import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import testQuestions from './data/testQuestions.json';
import { useEffect, useState } from 'react';

function Dashboard() {
  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-4">AdaptiveLearning Platform</h1>
      <p className="text-gray-600 mb-6">
        Adaptive learning for neurodivergent students using Muse headbands and facial recognition
      </p>
      <Link to="/practice" className="bg-blue-600 text-white px-6 py-3 rounded inline-block">
        Start Practice
      </Link>
      </div>
  );
}

function Practice() {

  /*temporary - import random question from JSON*/
  const [currentQuestion, setCurrentQuestion] = useState(() => pickRandomQuestion());
  const [result, setResult] = useState<boolean | null>(null);
  
  const [accuracy, setAccuracy] = useState<number>(0);
  const [totalQuestions, setTotalQuestions] = useState<number>(0);
  const [correctAnswers, setCorrectAnswers] = useState<number>(0);
  const [firstAttempt, setFirstAttempt] = useState(true);


  const questionText = currentQuestion.QuestionText;
  const options = currentQuestion.Options;

  function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const selectedOption = formData.get('option');

    const isCorrect = selectedOption === currentQuestion.Answer;

    setResult(isCorrect); 
    
    // Only count stats on first attempt
    if (firstAttempt) {
      setTotalQuestions(prev => prev + 1);

      if (isCorrect) {
        setCorrectAnswers(prev => prev + 1);
      }

      setFirstAttempt(false); // lock further attempts
    }
  }

    //calculate accuracy
    useEffect(() => {
      if (totalQuestions > 0) {
        setAccuracy((correctAnswers / totalQuestions) * 100);
      }
    }, [totalQuestions, correctAnswers]);
  


  return (
    <div className="p-8 max-w-4xl mx-auto">
      
      <div className = "flex mb-6 flex-wrap" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
      <h1 className="text-3xl font-bold">Practice Session</h1>
      <p className="text-gray-600">Accuracy: {accuracy.toFixed(2)}%</p>
      </div>

      <div className="bg-white shadow rounded-lg p-6 max-w-2xl">
        <p className="text-xl mb-4">{questionText}</p>
        <form onSubmit={handleSubmit}>
        <div className="space-y-2">
          {options.map((option: string, index: number) => (
              <div key={index}>
                <input
                  type="radio"
                  name="option"
                  id={`option${index}`}
                  value={option}
                />
                <label htmlFor={`option${index}`}>{option}</label>
        </div>
          ))}
        </div>


        <div className="mt-6">
          <button type = "submit" className="bg-green-600 text-white px-4 py-2 rounded mr-4">Submit</button>
        </div>
        </form>
      </div>

      {/* Display result */}
      {result === true && <p style = {{color: 'green'}} className="mt-4 font-bold">Correct!</p>}
      {result === false && <p style = {{color: 'red'}} className="mt-4 font-bold">Incorrect.</p>}
      {result !== null && <button onClick={() => { setCurrentQuestion(() => pickRandomQuestion()); setResult(null); setFirstAttempt(true); }} className="bg-blue-600 text-white px-4 py-2 rounded mt-4">Try Another Question</button>}  {/*Set result to null and generate new question*/}
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-blue-600 text-white p-4">
          <div className="flex gap-6">
            <Link to="/" className="font-bold text-xl">🧠 AdaptiveLearning</Link>
            <Link to="/practice" className="hover:underline">Practice</Link>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/practice" element={<Practice />} />
        </Routes>
      </div>
    </Router>
  );
}

function pickRandomQuestion() {
  const length = testQuestions.length;
  const randomIndex = Math.floor(Math.random() * length);
  return testQuestions[randomIndex].Question;

}


export default App;