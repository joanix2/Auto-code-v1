import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useState } from "react";
import Login from "./pages/Login";
import Projects from "./pages/Projects";
import CreateTicket from "./pages/CreateTicket";
import "./App.css";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem("githubToken") !== null;
  });
  const [githubToken, setGithubToken] = useState(() => {
    return localStorage.getItem("githubToken") || "";
  });

  const handleLogin = (token) => {
    localStorage.setItem("githubToken", token);
    setGithubToken(token);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("githubToken");
    setGithubToken("");
    setIsAuthenticated(false);
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/projects" /> : <Login onLogin={handleLogin} />} />
        <Route path="/projects" element={isAuthenticated ? <Projects token={githubToken} onLogout={handleLogout} /> : <Navigate to="/login" />} />
        <Route path="/create-ticket" element={isAuthenticated ? <CreateTicket token={githubToken} onLogout={handleLogout} /> : <Navigate to="/login" />} />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;
