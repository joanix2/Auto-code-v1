import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium'
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [ticketUrl, setTicketUrl] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.description) {
      setMessage({ type: 'error', text: 'Please fill in all required fields' });
      return;
    }

    setLoading(true);
    setMessage(null);
    setTicketUrl(null);

    try {
      const response = await axios.post(`${API_URL}/tickets`, {
        title: formData.title,
        description: formData.description,
        labels: ['auto-generated'],
        priority: formData.priority
      });

      setMessage({
        type: 'success',
        text: `Ticket created successfully! Your AI agent will start working on it shortly.`
      });
      setTicketUrl(response.data.ticket_url);
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        priority: 'medium'
      });

    } catch (error) {
      console.error('Error creating ticket:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to create ticket. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="header">
        <h1>🤖 Auto-Code Platform</h1>
        <p>AI-Powered Development Agent System</p>
        <p style={{ fontSize: '0.9rem', marginTop: '10px' }}>
          Create development tickets from your mobile device
        </p>
      </div>

      <div className="container">
        {message && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
            {ticketUrl && (
              <div style={{ marginTop: '10px' }}>
                <a href={ticketUrl} target="_blank" rel="noopener noreferrer" className="ticket-link">
                  View Ticket on GitHub →
                </a>
              </div>
            )}
          </div>
        )}

        <div className="card">
          <h2 style={{ marginBottom: '20px', color: '#333' }}>Create New Task</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="title">Task Title *</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="e.g., Add user authentication feature"
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Task Description *</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe what you want the AI agent to implement..."
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="priority">Priority</label>
              <select
                id="priority"
                name="priority"
                value={formData.priority}
                onChange={handleChange}
                disabled={loading}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            <button type="submit" className="button" disabled={loading}>
              {loading ? 'Creating Ticket...' : '🚀 Create Task'}
            </button>
          </form>
        </div>

        <div className="card" style={{ backgroundColor: '#f8f9fa' }}>
          <h3 style={{ marginBottom: '15px', color: '#333' }}>How it works</h3>
          <ol style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
            <li>Submit a development task from this PWA</li>
            <li>A GitHub issue is automatically created</li>
            <li>The task is queued via RabbitMQ</li>
            <li>An AI agent picks up the task and starts coding</li>
            <li>A pull request is created with the changes</li>
            <li>Review and merge when ready!</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default App;
