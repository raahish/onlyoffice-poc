import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      navigate('/');
      return;
    }
    fetch(`http://localhost:5001/projects?token=${token}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'error') {
          alert(data.message);
          navigate('/');
        } else {
          setProjects(data);
        }
      })
      .catch((err) => {
        console.error('Error fetching projects:', err);
        alert('Failed to fetch projects');
      });
  }, [token, navigate]);

  return (
    <div style={{ margin: '20px' }}>
      <h2>My Projects</h2>
      <ul>
        {projects.map((p) => (
          <li key={p.project_id}>
            <button onClick={() => navigate(`/projects/${p.project_id}`)}>
              {p.project_name}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}