# ONLYOFFICE PoC: Flask + React + Local Docs

This project demonstrates how to:

1. **Log in** as a user.
2. **List** projects from an in-memory store.
3. **Embed** an ONLYOFFICE document editor in React, pointing to a local `.docx`.
4. **Callback** changes from the Document Server back to Flask to save updated documents.
5. **Enable or Disable JWT** as needed.
6. **Use Ngrok** so the Document Server can reach your local Flask server for callbacks and downloads (useful if running in Docker with no direct route to localhost).

---

## Overview

- **Backend**: **Flask** (Python) on port `5001`.  
- **Frontend**: **React** on port `3000`.  
- **Data Store**: Simple in-memory dictionaries (users, projects, docs).  
- **File Storage**: Local folder `docs/` containing `.docx` files.  
- **ONLYOFFICE Docs**: Docker container on port `80` (Developer Edition with `license.lic`).  
- **Ngrok**: Tunnels localhost:5001 to a public URL so the container can access the Flask server callbacks.  

**Key Tools**:

- **Python 3.9+**
- **Node.js** and **npm** (or **yarn**)
- **Docker** (for ONLYOFFICE)
- **Ngrok** (to expose your local Flask server)
- **`license.lic`** if using Developer Edition

---

## 1. Architecture & Components

```
             [ React: localhost:3000 ]
                        |
                        | (HTTP calls)
                        v
          [ Flask: localhost:5001 or via NGROK tunnel ] ----> [ docs/ folder ]
                        ^
                        | (callback & file download)
                        v
[ ONLYOFFICE Docs (Docker) on localhost:80 ]  <---  possibly needs ngrok-based URL for callbacks
```

1. **React**:
   - Renders login and project screens.
   - Fetches doc config from Flask at `http://localhost:5001`.
   - Displays the embedded ONLYOFFICE editor via `@onlyoffice/document-editor-react`.

2. **Flask**:
   - Validates user login.
   - Returns doc config (with doc URL & callback URL).
   - Hosts `.docx` files in a `docs/` folder.
   - Receives callback from the Document Server to save updated docs.

3. **ONLYOFFICE Docker**:
   - Developer Edition with or without JWT.  
   - Port `80` mapped to your Mac or PC’s `localhost:80`.

4. **Ngrok** (if needed):
   - Creates a public URL to the Flask server so the Docker container can call back or download `.docx` from your local environment.

---

## 2. Functional Requirements

1. **User Login**:
   - Simple credentials: e.g., “alice” / “pass123”.

2. **Project List**:
   - Each user sees only the projects in which they’re listed.

3. **View/Edit DOCX**:
   - Clicking a project opens the `.docx` in ONLYOFFICE for real-time editing.
   - Edits are saved automatically to your local `docs/` folder.

4. **Callback Handling**:
   - ONLYOFFICE calls `POST /onlyoffice/callback` when the doc is ready or auto-saved.
   - Flask downloads the updated `.docx` from the server’s cache URL.

5. **JWT**:
   - Disabled by default (`JWT_ENABLED=false`).
   - Optionally enable for production. If enabled, **every** config/callback must be signed with the correct secret.

6. **Use of Ngrok**:
   - If your Docker container cannot directly reach `http://localhost:5001`, you can run `ngrok http 5001` and replace all “localhost:5001” references in the doc config with your `*.ngrok-free.app` domain.

---

## 3. Implementation Steps

### 3.1 Set Up ONLYOFFICE Docker (Developer Edition)

1. **Download** or **pull** the Developer Edition Docker image:
   ```bash
   docker pull onlyoffice/documentserver-de
   ```
2. **Create** local folders for persistent data (optional but recommended):
   ```bash
   mkdir -p ~/onlyoffice/DocumentServer/data
   mkdir -p ~/onlyoffice/DocumentServer/logs
   mkdir -p ~/onlyoffice/DocumentServer/lib
   mkdir -p ~/onlyoffice/DocumentServer/db
   ```
3. **Place** your `license.lic` in `~/onlyoffice/DocumentServer/data` if you have it.

4. **Run** the container:

   ```bash
   docker run -i -t -d -p 80:80 --restart=always \
     -v ~/onlyoffice/DocumentServer/logs:/var/log/onlyoffice \
     -v ~/onlyoffice/DocumentServer/data:/var/www/onlyoffice/Data \
     -v ~/onlyoffice/DocumentServer/lib:/var/lib/onlyoffice \
     -v ~/onlyoffice/DocumentServer/db:/var/lib/postgresql \
     -e JWT_ENABLED=false \
     onlyoffice/documentserver-de
   ```

   > **Note**: We set `JWT_ENABLED=false` for local development. For production, consider setting `-e JWT_ENABLED=true -e JWT_SECRET=<your-secret>`.

5. Check `http://localhost` in a browser to see if ONLYOFFICE loads.

---

### 3.2 Run Flask

1. **Create** a folder `server/` with `app.py`.
2. **Install** dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install flask flask-cors requests pyjwt
   ```
3. **Ensure** `docs/` folder has `abc.docx` or `xyz.docx`.
4. **Start** Flask:
   ```bash
   python app.py
   ```
5. By default, it runs on `http://localhost:5001`.

---

### 3.3 (Optional) Use Ngrok

If the Docker container cannot access your Mac/PC’s `localhost:5001`:

1. **Install** ngrok from [ngrok.com](https://ngrok.com/).
2. **Run**:
   ```bash
   ngrok http 5001
   ```
3. You get a public URL, e.g., `https://c3ca-70-23-89-167.ngrok-free.app`.
4. **Replace** references in your Flask code for `callbackUrl` and `download` with the ngrok domain. Then the Docker container can call those URLs.

---

### 3.4 Run React

1. **Create** the React app in a `client/` folder:
   ```bash
   cd client
   npx create-react-app .
   npm install --save react-router-dom @onlyoffice/document-editor-react
   ```
2. **Update** code:
   - `Login.js`: for user login.
   - `Projects.js`: to list user’s projects.
   - `EditorPage.js`: uses `<DocumentEditor />` from `@onlyoffice/document-editor-react`.
3. **Start** React:
   ```bash
   npm start
   ```
4. Open `http://localhost:3000` in a browser to see the login page.

---

### 3.5 Testing the Flow

1. **Log in** as `alice` or `bob`.
2. **Pick** a project (e.g., “abc”).
3. **React** fetches doc config from Flask (`/projects/abc/document-config?token=...`).
4. **ONLYOFFICE** fetches the `.docx` from the `docs/` folder via Flask, loads it in the editor.
5. **Make edits**; the Document Server eventually calls `POST /onlyoffice/callback?docId=abc`.
6. **Flask** overwrites `docs/abc.docx` with the updated version.

---

## 4. Code Files Summary

1. **`server/app.py`**  
   - Contains routes: `/login`, `/projects`, `/projects/<id>/document-config`, `/docs/<id>/download`, `/onlyoffice/callback`.
   - Optionally uses JWT if you enable it.

2. **`client/src/Login.js`**  
   - Simple login form, calls `POST /login`.

3. **`client/src/Projects.js`**  
   - Lists projects from `GET /projects?token=...`.

4. **`client/src/EditorPage.js`**  
   - Fetches doc config from Flask, then renders `<DocumentEditor .../>`.

5. **`client/docker-compose.yml`** (Optional)  
   - You can orchestrate containers if desired, but local usage is simpler for a PoC.

---

## 5. Future Enhancements

- **Enable JWT** in production. Set `JWT_ENABLED=true` in Docker and generate a secret with `-e JWT_SECRET=mySecretKey`.
- **Security**: Store user sessions securely, use hashed passwords, etc.
- **Database**: Switch from in-memory dictionaries to SQLite, PostgreSQL, or MongoDB.
- **Versioning**: Keep old versions of doc files instead of overwriting.  
- **HTTPS**: Use SSL certificates for Document Server, Flask, or both.

---

## 6. Conclusion

By following these steps, you’ll have a **local PoC** for collaborative DOCX editing:

1. **Flask** manages user login and data.  
2. **React** shows projects and embeds the official **ONLYOFFICE** React component.  
3. **ONLYOFFICE** (Developer Edition) in Docker handles real-time editing on port 80.  
4. **Ngrok** helps route callbacks if the container can’t reach localhost.  

This setup can be extended with real databases, JWT authentication, secure certificates, and production deployment as needed.