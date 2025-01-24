import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './Login';
import Projects from './Projects';
import EditorPage from './EditorPage';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:projectId" element={<EditorPage />} />
      </Routes>
    </Router>
  );
}
