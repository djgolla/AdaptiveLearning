import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

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
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Practice Session</h1>
      <div className="bg-white shadow rounded-lg p-6 max-w-2xl">
        <p className="text-xl mb-4">Sample Question Goes Here</p>
        <div className="space-y-2">
          <button className="w-full text-left p-3 border rounded hover:bg-gray-50">Option A</button>
          <button className="w-full text-left p-3 border rounded hover:bg-gray-50">Option B</button>
          <button className="w-full text-left p-3 border rounded hover:bg-gray-50">Option C</button>
          <button className="w-full text-left p-3 border rounded hover:bg-gray-50">Option D</button>
        </div>
      </div>
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

export default App;