import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DocumentEditor } from "@onlyoffice/document-editor-react";

export default function EditorPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem('token'); // user login token
  const [docConfig, setDocConfig] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate('/');
      return;
    }
    // 1) Fetch final config from Flask
    fetch(`http://localhost:5001/projects/${projectId}/document-config?token=${token}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === "error") {
          alert(data.message);
          navigate("/projects");
        } else {
          // data should contain:
          // {
          //   documentType: "word",
          //   type: "desktop",
          //   document: {fileType, key, title, url},
          //   editorConfig: {...},
          //   token: "JWT..."
          // }
          console.log("Received config from server:", data);
          setDocConfig(data);
        }
      })
      .catch(err => {
        console.error("Failed to get doc config:", err);
        alert("Document config failed to load");
      });
  }, [projectId, token, navigate]);

  const handleDocumentReady = () => {
    console.log("ONLYOFFICE editor: Document is ready");
  };

  const handleLoadComponentError = (errorCode, errorDescription) => {
    console.error("ONLYOFFICE load error:", errorCode, errorDescription);
    alert(`Error loading doc: ${errorDescription}`);
  };

  return (
    <div style={{ margin: "20px" }}>
      <h2>Editor Page: {projectId}</h2>
      <div style={{ width: "100%", height: "80vh" }}>
        {docConfig ? (
          <DocumentEditor
            id="docEditor"
            documentServerUrl="http://localhost" // Container mapped to port 80
            config={docConfig}
            events_onDocumentReady={handleDocumentReady}
            onLoadComponentError={handleLoadComponentError}
            width="100%"
            height="100%"
          />
        ) : (
          <p>Loading document config...</p>
        )}
      </div>
    </div>
  );
}