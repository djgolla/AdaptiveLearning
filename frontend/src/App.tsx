import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import testQuestions from './data/testQuestions.json';
import { useState } from 'react';

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

  const questionText = currentQuestion.QuestionText;
  const options = [
    currentQuestion.Options[0],
    currentQuestion.Options[1],
    currentQuestion.Options[2],
    currentQuestion.Options[3]
  ];

  function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const selectedOption = formData.get('option');

    setResult(selectedOption === currentQuestion.Answer); 
  }


  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Practice Session</h1>
      
      <div className="bg-white shadow rounded-lg p-6 max-w-2xl">
        <p className="text-xl mb-4">{questionText}</p>
        <form onSubmit={handleSubmit}>
        <div className="space-y-2">
          <input type = "radio" name="option" id="option1" value={options[0]}/>
          <label htmlFor="option1">{options[0]}</label>
          <input type = "radio" name="option" id="option2" value={options[1]}/>
          <label htmlFor="option2">{options[1]}</label>
          <input type = "radio" name="option" id="option3" value={options[2]}/>
          <label htmlFor="option3">{options[2]}</label>
          <input type = "radio" name="option" id="option4" value={options[3]}/>
          <label htmlFor="option4">{options[3]}</label>
        </div>

        <div className="mt-6">
          <button type = "submit" className="bg-green-600 text-white px-4 py-2 rounded mr-4">Submit</button>
        </div>
        </form>
      </div>

      {/* Display result */}
      {result === true && <p style = {{color: 'green'}} className="mt-4 font-bold">Correct!</p>}
      {result === false && <p style = {{color: 'red'}} className="mt-4 font-bold">Incorrect.</p>}
      {result !== null && <button onClick={() => { setCurrentQuestion(() => pickRandomQuestion()); setResult(null); }} className="bg-blue-600 text-white px-4 py-2 rounded mt-4">Try Another Question</button>}  {/*Set result to null and generate new question*/}
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