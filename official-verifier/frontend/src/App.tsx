import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Entity from './pages/Entity';
import Submit from './pages/Submit';
import Claim from './pages/Claim';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                🔒 Official Website Verifier
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <a href="/" className="text-gray-700 hover:text-gray-900">
                Home
              </a>
              <a href="/submit" className="text-gray-700 hover:text-gray-900">
                Submit
              </a>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/entity/:id" element={<Entity />} />
          <Route path="/submit" element={<Submit />} />
          <Route path="/claim" element={<Claim />} />
        </Routes>
      </main>

      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 text-sm">
            Official Website Verification Platform - Protecting users from scams
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
