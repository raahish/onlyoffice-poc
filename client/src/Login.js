import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('http://localhost:5001/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'ok') {
          localStorage.setItem('token', data.token);
          navigate('/projects');
        } else {
          alert('Login failed');
        }
      })
      .catch((err) => {
        console.error('Login error:', err);
        alert('Failed to connect to server.');
      });
  };

  return (
    <div style={{ margin: '20px' }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username: </label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div style={{ marginTop: '10px' }}>
          <label>Password: </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button type="submit" style={{ marginTop: '10px' }}>Login</button>
      </form>
    </div>
  );
}