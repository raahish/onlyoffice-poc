import os
import uuid
import time
import jwt  # PyJWT
import requests

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

############################################################################
# FLASK CONFIG
############################################################################
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Must match the environment variable in your ONLYOFFICE container
# e.g. docker run -p 80:80 -e JWT_ENABLED=true -e JWT_SECRET=someSecret onlyoffice/documentserver-de
JWT_SECRET = "737f0df4938974f01aaf6349f640160041ea416c92a58aef22b0ae54cfb5eeb6c5f69d4070846bac428b45e8cec145d1e9e4952f96d38dc5447d99953d6af338"
JWT_ALGORITHM = "HS256"

HOST = "0.0.0.0"
PORT = 5001
app.secret_key = "someFlaskSecret"  # for session usage if needed

############################################################################
# In-Memory Data
############################################################################
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

############################################################################
# JWT UTILS
############################################################################
def generate_jwt(payload: dict) -> str:
    """
    Generate a JWT that ONLYOFFICE Document Server accepts.
    Must match the Document Server's JWT_SECRET.
    """
    payload["iat"] = int(time.time())
    payload["exp"] = int(time.time()) + 60*30  # 30 minutes
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt(token: str) -> dict:
    """
    Verify an incoming JWT from Document Server.
    Raises if invalid/expired.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

############################################################################
# FLASK ROUTES
############################################################################
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if username in users and users[username]["password"] == password:
        return jsonify({"status": "ok", "token": username})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@app.route("/projects", methods=["GET"])
def list_projects():
    user_token = request.args.get("token")
    if not user_token or user_token not in users:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    user_projects = []
    for pid, proj in projects.items():
        if user_token in proj["allowed_users"]:
            user_projects.append({
                "project_id": pid,
                "project_name": proj["project_name"]
            })
    return jsonify(user_projects)


@app.route("/projects/<project_id>/document-config", methods=["GET"])
def get_document_config(project_id):
    """
    Returns the final config object for the official React component or direct usage:
      - documentType: 'word'
      - type: 'desktop'  (optional but recommended)
      - token: <JWT>
    """
    user_token = request.args.get("token")
    if not user_token or user_token not in users:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    proj = projects.get(project_id)
    if not proj or user_token not in proj["allowed_users"]:
        return jsonify({"status": "error", "message": "Forbidden"}), 403

    doc_info = docs.get(project_id)
    if not doc_info:
        return jsonify({"status": "error", "message": "No doc found"}), 404

    # Unique key for each session
    doc_key = f"{doc_info['doc_id']}-{uuid.uuid4()}"

    # Optional local link token
    link_payload = {"file_path": doc_info["file_path"]}
    link_jwt = generate_jwt(link_payload)

    file_download_url = (
        f"https://c3ca-70-23-89-167.ngrok-free.app/docs/{project_id}/download"
        f"?token={user_token}"
        f"&jwt={link_jwt}"
    )

    # Build the config
    config = {
        # CRUCIAL: "documentType" at root
        "documentType": "word",
        # Additional optional param: "type": "desktop" if you want
        "type": "desktop",

        "document": {
            "fileType": "docx",
            "key": doc_key,
            "title": f"{proj['project_name']}.docx",
            "url": file_download_url
        },
        "editorConfig": {
            "callbackUrl": f"https://c3ca-70-23-89-167.ngrok-free.app/onlyoffice/callback?docId={project_id}",
            "lang": "en",
            "mode": "edit",
            "user": {
                "id": user_token,
                "name": user_token.capitalize()
            }
        }
    }

    # Top-level JWT for Document Server
    docserver_payload = {
        "document": {
            "fileType": "docx",
            "key": doc_key
        }
    }
    config["token"] = generate_jwt(docserver_payload)

    return jsonify(config)


@app.route("/docs/<doc_id>/download", methods=["GET"])
def download_document(doc_id):
    """
    Document Server fetches the .docx from here.
    We optionally verify a local link JWT in query param 'jwt'.
    """
    user_token = request.args.get("token")
    if not user_token or user_token not in users:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    # local_jwt = request.args.get("jwt")
    # if local_jwt:
    #     try:
    #         verify_jwt(local_jwt)
    #     except jwt.ExpiredSignatureError:
    #         return jsonify({"status": "error", "message": "Link JWT expired"}), 403
    #     except jwt.InvalidTokenError:
    #         return jsonify({"status": "error", "message": "Invalid link JWT"}), 403

    doc_info = docs.get(doc_id)
    if not doc_info:
        return jsonify({"status": "error", "message": "Doc not found"}), 404

    proj = projects.get(doc_info["project_id"])
    if user_token not in proj["allowed_users"]:
        return jsonify({"status": "error", "message": "Forbidden"}), 403

    file_path = doc_info["file_path"]
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "File not found"}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{proj['project_name']}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.route("/onlyoffice/callback", methods=["POST"])
def onlyoffice_callback():
    """
    Document Server calls this with a JWT in Authorization: Bearer <token>
    """
    doc_id = request.args.get("docId")
    data = request.json or {}
    status_code = data.get("status")

    auth_header = request.headers.get("Authorization", "")
    # if not auth_header.startswith("Bearer "):
    #     return jsonify({"error": 1, "message": "No Bearer token"}), 403

    # callback_jwt = auth_header.replace("Bearer ", "")
    # try:
    #     decoded = verify_jwt(callback_jwt)
    #     # optionally match doc_id with decoded["document"]["key"]
    # except jwt.ExpiredSignatureError:
    #     return jsonify({"error": 1, "message": "JWT token expired"}), 403
    # except jwt.InvalidTokenError:
    #     return jsonify({"error": 1, "message": "Invalid JWT token"}), 403

    # If doc is ready to save
    if status_code == 2:
        download_url = data.get("url")
        if download_url:
            updated_file = requests.get(download_url).content
            doc_info = docs.get(doc_id)
            if doc_info:
                with open(doc_info["file_path"], "wb") as f:
                    f.write(updated_file)
                doc_info["version"] += 1
        return jsonify({"error": 0})

    return jsonify({"error": 0})


if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    print(f"Flask server on http://localhost:{PORT}")
    print(f"JWT_SECRET = {JWT_SECRET}")
    app.run(host=HOST, port=PORT, debug=True)
