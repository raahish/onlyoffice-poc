Below is a **Product Requirements Document (PRD)** for a **Proof of Concept (PoC)** application demonstrating an **ONLYOFFICE** integration using **Flask**, **ReactJS**, a **local database**, and a **local file system** for document storage. This PRD includes:

1. **High-level architecture**  
2. **Functional requirements**  
3. **Data structures** and **class/module definitions**  
4. **Detailed workflow**  
5. **Implementation plan** (step-by-step) suitable for beginners.

The end result is a functioning prototype that a developer with **little coding experience** could follow to demonstrate collaborative document editing for DOCX files.

---

# 1. Overview

This PoC (Proof of Concept) app will:

1. **Allow a user to log in** with simple credentials.  
2. **Display a list of projects** that the user can access.  
3. **Show the most recent DOCX document** for the selected project.  
4. **Open the document** in an embedded **ONLYOFFICE** editor for real-time (collaborative) editing.  
5. **Save changes** automatically and store them on the **local file system**, updating project metadata in a **local database**.

**Key Tools**:
- **Backend**: Python **Flask**  
- **Frontend**: **ReactJS**  
- **Database**: SQLite (local DB) or an in-memory Python dictionary (for simplicity).  
- **Document Storage**: Local file system (e.g., a folder named `docs/`).  
- **ONLYOFFICE Document Server**: Docker container on `localhost` (port 8080).  

---

# 2. Architecture & Components

## 2.1. Overall Diagram

```
   [React App: localhost:3000]    <--->     [Flask: localhost:5000]     <--->  [Local DB + docs/ folder]
                                \                     ^
                                 \ (HTTP calls)       |
                                  \                   | (Callback from Doc Server)
                                   \                  v
                                    [ONLYOFFICE Document Server: localhost:8080]
```

1. **React** (Port **3000**): Renders UI (login screen, project list, document editor).  
2. **Flask** (Port **5000**): Provides APIs:
   - `POST /login`  
   - `GET /projects`  
   - `GET /projects/<project_id>/document-config`  
   - `GET /docs/<doc_id>/download`  
   - `POST /onlyoffice/callback`  
3. **Local DB**: Simple storage for users, projects, and documents. Could be **SQLite** or a Python dictionary.  
4. **Local File System** (`docs/` folder): Where DOCX files are saved/retrieved.  
5. **ONLYOFFICE Document Server** (Port **8080**): Runs in Docker locally, handles the collaborative editing.  

---

## 2.2. Components Breakdown

1. **React Frontend**  
   - **Login Page** (user enters username/password).  
   - **Project List Page** (shows the projects the user can access).  
   - **Document Editor Page** (initializes the ONLYOFFICE editor).  

2. **Flask Backend**  
   - **User Management**: A simple in-memory store or DB table for users.  
   - **Project Management**: Each project has an ID, a list of user IDs who can access it.  
   - **Document Management**: Each project has at least one DOCX file (the latest version is stored at `docs/<project_id>.docx`).  
   - **OnlyOffice Integration**: Endpoints that generate config for the Document Server and handle callback.

3. **Local Database**  
   - Could be **SQLite** or **JSON**/in-memory for simplicity.  
   - Stores 3 main tables/collections:
     - **users**: (username, password)  
     - **projects**: (project_id, project_name, allowed_users)  
     - **docs**: (doc_id, project_id, version, filepath, last_modified)  
       - For this PoC, we can store only **1 doc** per project for simplicity.  

4. **docs/ Folder**  
   - Each project’s DOCX is stored as `<project_id>.docx` or `<project_id>_v2.docx`, etc.  
   - On every save, the file is overwritten or a new version is created.  

---

# 3. Functional Requirements

1. **User Login**  
   - The user must be able to enter a username and password on the frontend.  
   - The backend must verify credentials and establish a simple session or token.

2. **Project List**  
   - The user sees only the projects that match their `username` in the project’s `allowed_users`.

3. **View & Edit Latest Document**  
   - When a user selects a project, the app fetches the **most recent DOCX** for that project.  
   - The user can click “Open Editor” to load it in the ONLYOFFICE editor.  

4. **ONLYOFFICE Editing**  
   - The Document Server (running on `localhost:8080`) loads the file from the Flask route.  
   - Changes are saved automatically (status=2 callback).  
   - The updated file is stored back into `docs/` folder with the same or incremented version name.  
   - The user sees the updated content upon re-opening the doc.

5. **Collaborative Editing**  
   - If multiple users open the same project doc, they should see each other’s edits in real time.  
   - This is handled automatically by ONLYOFFICE if the doc has the same `document.key` for all users who open it simultaneously.

---

# 4. Data Structures & Classes

## 4.1. Data Model (Python side)

For demonstration, we can define three main dictionaries or tables:

1. **users**  
   ```python
   users = {
     "alice": {"password": "pass123"},
     "bob": {"password": "qwerty"}
   }
   ```

2. **projects**  
   ```python
   projects = {
     "abc": {
       "project_name": "Project ABC",
       "allowed_users": ["alice", "bob"]
     },
     "xyz": {
       "project_name": "Project XYZ",
       "allowed_users": ["alice"]
     }
   }
   ```

3. **docs**  
   ```python
   docs = {
     "abc": {
       "doc_id": "abc",
       "project_id": "abc",
       "file_path": "docs/abc.docx",
       "version": 1,
       "last_modified": "2025-01-01T12:00:00"
     },
     "xyz": {
       "doc_id": "xyz",
       "project_id": "xyz",
       "file_path": "docs/xyz.docx",
       "version": 1,
       "last_modified": "2025-01-01T12:00:00"
     }
   }
   ```

*(You can store these in a small SQLite DB if you prefer. The logic remains the same.)*

## 4.2. Flask Modules & Functions

1. `app.py` (main Flask file)  
   - **UserRoutes** (for login)  
   - **ProjectRoutes** (for listing projects)  
   - **DocumentRoutes** (OnlyOffice integration: config endpoint, file download, callback)  

2. **Utility Functions**:  
   - `check_login(username, password)` -> returns True/False  
   - `get_projects_for_user(username)` -> returns list of project IDs  
   - `get_doc_for_project(project_id)` -> returns doc record from `docs` dictionary  

---

# 5. Detailed Workflows

## 5.1. User Login Flow

1. **React** displays a login form (`username`, `password`).  
2. On submit, React calls `POST /login` with the credentials.  
3. **Flask** checks if `(username, password)` matches any entry in `users`.  
4. If valid, Flask sets a simple session cookie or returns a success JSON with a token.  
5. React stores that token in local state (or context).  

## 5.2. Project List Flow

1. **React** calls `GET /projects` with the user’s token or session.  
2. **Flask** decodes the user from the session or token.  
3. Flask returns the projects from `projects` dictionary where `username` is in `allowed_users`.  
4. **React** displays these projects in a list.  

## 5.3. Loading & Editing Document

1. **React** calls `GET /projects/<project_id>/document-config`  
   - The request includes the user’s token.  
2. **Flask** checks if the user is allowed to see `<project_id>`.  
3. **Flask** finds the doc in `docs[project_id]`.  
4. **Flask** generates a unique `document.key` (e.g., `abc-<uuid>`).  
5. **Flask** forms a `document.url` pointing to `/docs/<project_id>/download`.  
6. **Flask** sets `editorConfig.callbackUrl` to `/onlyoffice/callback?docId=<project_id>`.  
7. **React** receives this JSON config.  
8. **React** then calls `new window.DocEditor("editorContainer", config)` to open the doc in the ONLYOFFICE editor.  
9. **ONLYOFFICE** fetches the doc from `GET /docs/<project_id>/download`.  
10. The user edits the doc, with changes sync’d in real time.

## 5.4. Saving Updates (Callback)

1. The Document Server autosaves or final saves the doc.  
2. Document Server POSTs to `POST /onlyoffice/callback?docId=<project_id>` with a JSON body that includes:
   - `status: 2` when file is ready  
   - `url` to download the updated file from the Document Server’s internal cache  
3. **Flask** downloads the file from `url`.  
4. **Flask** overwrites `docs/abc.docx` or increments a version if needed.  
5. **Flask** updates `docs[project_id]["version"] += 1`.  
6. **Flask** returns `{"error": 0}` to indicate success.

---

# 6. Step-by-Step Implementation Guide

Below is an **implementation plan** that someone with minimal coding background can follow. It assumes you have:

- **Node.js** and **npm** (for React)  
- **Python** 3.9+  
- **Docker** (for ONLYOFFICE)

## 6.1. Setup ONLYOFFICE Document Server Locally

1. Install Docker (if not already installed).  
2. Pull and run the Document Server container:
   ```bash
   docker pull onlyoffice/documentserver:latest
   docker run -i -t -d --name onlyoffice -p 8080:80 onlyoffice/documentserver
   ```
3. Verify it’s running at `http://localhost:8080`.

## 6.2. Create Flask Backend

1. **Create a folder** `server/`, and inside it a file called `app.py`.  
2. **Initialize** with minimal code:

   ```python
   from flask import Flask, request, jsonify, send_file
   import os, uuid, requests

   app = Flask(__name__)
   app.secret_key = "someSecretKey"  # for session management

   # In-memory data
   users = {
       "alice": {"password": "pass123"},
       "bob": {"password": "qwerty"}
   }

   projects = {
       "abc": {
           "project_name": "Project ABC",
           "allowed_users": ["alice", "bob"]
       },
       "xyz": {
           "project_name": "Project XYZ",
           "allowed_users": ["alice"]
       }
   }

   docs = {
       "abc": {
           "doc_id": "abc",
           "project_id": "abc",
           "file_path": "docs/abc.docx",
           "version": 1
       },
       "xyz": {
           "doc_id": "xyz",
           "project_id": "xyz",
           "file_path": "docs/xyz.docx",
           "version": 1
       }
   }

   @app.route('/login', methods=['POST'])
   def login():
       data = request.json
       username = data.get('username')
       password = data.get('password')
       if username in users and users[username]["password"] == password:
           # For simplicity, let's just return a success JSON with the username as token
           return jsonify({"status": "ok", "token": username})
       return jsonify({"status": "error", "message": "Invalid credentials"}), 401


   @app.route('/projects', methods=['GET'])
   def list_projects():
       # Expect a 'token' query param or something similar
       token = request.args.get('token')
       if not token or token not in users:
           return jsonify({"status": "error", "message": "Not authenticated"}), 401

       user_projects = []
       for pid, proj in projects.items():
           if token in proj["allowed_users"]:
               user_projects.append({
                   "project_id": pid,
                   "project_name": proj["project_name"]
               })
       return jsonify(user_projects)


   @app.route('/projects/<project_id>/document-config', methods=['GET'])
   def get_document_config(project_id):
       token = request.args.get('token')
       if not token or token not in users:
           return jsonify({"status": "error", "message": "Not authenticated"}), 401

       # Check if user can access this project
       proj = projects.get(project_id)
       if not proj or token not in proj["allowed_users"]:
           return jsonify({"status": "error", "message": "Forbidden"}), 403

       doc_info = docs.get(project_id)
       if not doc_info:
           return jsonify({"status": "error", "message": "No doc found"}), 404

       # Generate unique key
       doc_key = f"{doc_info['doc_id']}-{uuid.uuid4()}"

       # Build config
       config = {
           "document": {
               "title": f"{proj['project_name']}.docx",
               "url": f"http://localhost:5000/docs/{project_id}/download?token={token}",
               "fileType": "docx",
               "key": doc_key
           },
           "editorConfig": {
               "callbackUrl": f"http://localhost:5000/onlyoffice/callback?docId={project_id}",
               "lang": "en",
               "mode": "edit",
               "user": {
                   "id": token,
                   "name": token.capitalize()
               }
           }
       }
       return jsonify(config)


   @app.route('/docs/<doc_id>/download', methods=['GET'])
   def download_document(doc_id):
       token = request.args.get('token')
       if not token or token not in users:
           return jsonify({"status": "error", "message": "Not authenticated"}), 401

       doc_info = docs.get(doc_id)
       if not doc_info:
           return jsonify({"status": "error", "message": "Doc not found"}), 404

       # Extra security check: confirm token can access doc's project
       project = projects.get(doc_info["project_id"])
       if token not in project["allowed_users"]:
           return jsonify({"status": "error", "message": "Forbidden"}), 403

       # Return the file
       file_path = doc_info["file_path"]
       if os.path.exists(file_path):
           return send_file(file_path, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
       else:
           return jsonify({"status": "error", "message": "File not found"}), 404


   @app.route('/onlyoffice/callback', methods=['POST'])
   def onlyoffice_callback():
       doc_id = request.args.get("docId")
       data = request.json
       status = data.get("status")
       if status == 2:
           download_url = data.get("url")
           if download_url:
               # Download updated file from Document Server
               updated_content = requests.get(download_url).content

               # Overwrite local doc
               doc_info = docs.get(doc_id)
               if doc_info:
                   file_path = doc_info["file_path"]
                   with open(file_path, "wb") as f:
                       f.write(updated_content)
                   # Increment version
                   doc_info["version"] += 1
                   return jsonify({"error": 0})
       return jsonify({"error": 0})

   if __name__ == "__main__":
       # Make sure your docs/ folder exists
       os.makedirs("docs", exist_ok=True)
       # In real usage, you'd need actual docx files in "docs/abc.docx" etc.
       app.run(host="0.0.0.0", port=5000, debug=True)
   ```

3. **Run** it: `python app.py`  
   - This starts your Flask server at `http://localhost:5000`.

## 6.3. Create React App

1. **Create a folder** `client/` and run `npx create-react-app .` or similar.  
2. **In `public/index.html`**, add the ONLYOFFICE script tag:

   ```html
   <script src="http://localhost:8080/web-apps/apps/api/documents/api.js"></script>
   ```

3. **In `src/App.js`**, create the login, project list, and editor pages.

### 6.3.1 `src/App.js` (Simple Routing)

```jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './Login';
import Projects from './Projects';
import EditorPage from './EditorPage';

function App() {
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

export default App;
```

### 6.3.2 `src/Login.js`

```jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('http://localhost:5000/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password})
    })
    .then(res => res.json())
    .then(data => {
      if(data.status === 'ok') {
        // save token
        localStorage.setItem('token', data.token);
        navigate('/projects');
      } else {
        alert('Login failed');
      }
    });
  };

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username: </label>
          <input value={username} onChange={(e)=> setUsername(e.target.value)} />
        </div>
        <div>
          <label>Password: </label>
          <input type="password" value={password} onChange={(e)=> setPassword(e.target.value)} />
        </div>
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;
```

### 6.3.3 `src/Projects.js`

```jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const token = localStorage.getItem('token');

  useEffect(() => {
    if(!token) {
      navigate('/');
      return;
    }
    fetch(`http://localhost:5000/projects?token=${token}`)
      .then(res => res.json())
      .then(data => {
        if(data.status === 'error') {
          alert(data.message);
          navigate('/');
        } else {
          setProjects(data);
        }
      });
  }, [token, navigate]);

  return (
    <div>
      <h2>My Projects</h2>
      <ul>
        {projects.map(p => (
          <li key={p.project_id}>
            <button onClick={()=> navigate(`/projects/${p.project_id}`)}>
              {p.project_name}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Projects;
```

### 6.3.4 `src/EditorPage.js`

```jsx
import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function EditorPage() {
  const { projectId } = useParams();
  const token = localStorage.getItem('token');
  const navigate = useNavigate();

  useEffect(() => {
    if(!token) {
      navigate('/');
      return;
    }

    // 1) Fetch ONLYOFFICE config
    fetch(`http://localhost:5000/projects/${projectId}/document-config?token=${token}`)
      .then(res => res.json())
      .then(config => {
        if(config.status === 'error') {
          alert(config.message);
          navigate('/projects');
        } else {
          // 2) Initialize the ONLYOFFICE editor
          if(window.DocEditor) {
            new window.DocEditor('editorContainer', config);
          } else {
            console.error("ONLYOFFICE script not loaded or DocEditor not found");
          }
        }
      });
  }, [projectId, token, navigate]);

  return (
    <div>
      <h2>Editor Page: {projectId}</h2>
      <div id="editorContainer" style={{ width: '100%', height: '80vh' }} />
    </div>
  );
}

export default EditorPage;
```

4. **Run** `npm start` (or `yarn start`) in `client/`.

## 6.4. Testing the Flow

1. **Ensure** the Document Server is running: `docker ps` shows `onlyoffice`.  
2. **Ensure** Flask is running: `python app.py` on `localhost:5000`.  
3. **Ensure** React is running: `npm start` on `localhost:3000`.  
4. Go to **http://localhost:3000**:  
   - Log in as **alice** with password `pass123`.  
   - See 2 projects: “Project ABC” and “Project XYZ.”  
   - Click “Project ABC.”  
   - The React app fetches the doc config and calls the Document Server to open `docs/abc.docx`.  
   - If you place an actual `abc.docx` in the `docs/` folder, you should see it load.  
   - Edit away!  

5. **Collaborative**:  
   - Open another browser/incognito window, log in as “bob” with password `qwerty`.  
   - Also open “Project ABC.”  
   - Now, both windows see each other’s changes in real time (assuming the Document Server is working properly).  

---

# 7. Documentation & GitHub Repo Structure

A suggested **repo structure**:

```
my-onlyoffice-poc
│   README.md
├── server
│   ├── app.py
│   └── docs/ (place docx files here)
├── client
│   ├── package.json
│   ├── public
│   │   └── index.html (with the <script> for OnlyOffice)
│   └── src
│       ├── App.js
│       ├── Login.js
│       ├── Projects.js
│       ├── EditorPage.js
│       └── ...
└── docker-compose.yml (optional)
```

## 7.1. README Documentation

In `README.md`, include:

1. **Setup Steps**:
   - How to run the Document Server (`docker run ...`)  
   - How to run Flask (`python app.py`)  
   - How to run React (`npm start`)  

2. **User Credentials**:
   - `alice / pass123`  
   - `bob / qwerty`  

3. **Sample Project & Doc**:
   - Place a sample `abc.docx` in `docs/abc.docx`.

4. **Usage**:
   - Login flow  
   - Opening a project  
   - Editing the doc  

5. **Future Enhancements**:
   - Move from in-memory data to SQLite or MongoDB.  
   - Add real authentication (JWT tokens, password hashing).  
   - Add versioning UI to see older versions, etc.

---

# 8. Conclusion

This **PRD** and **implementation guide** outline a complete, minimal PoC showing how to:

1. **Authenticate** users with Flask.  
2. **List** projects and associate them with users.  
3. **Embed** the **ONLYOFFICE editor** in React.  
4. **Handle** real-time collaboration with a callback-based save mechanism.  
5. **Store** DOCX files locally and keep a simple version count.