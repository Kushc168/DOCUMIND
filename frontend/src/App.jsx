import { useEffect, useMemo, useState } from "react";

const API_BASE = "http://localhost:8000";
const SIZE_LIMIT_MB = 50;

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export default function App() {
  const [mode, setMode] = useState("single");
  const [target, setTarget] = useState("pdf-to-word");
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [ocrStatus, setOcrStatus] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatBusy, setChatBusy] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatSessionId, setChatSessionId] = useState("");
  const [chatDocBusy, setChatDocBusy] = useState(false);
  const [chatSummaryBusy, setChatSummaryBusy] = useState(false);
  const [conversionHistory, setConversionHistory] = useState([]);
  const [historyOpen, setHistoryOpen] = useState(false);

  const totalSize = useMemo(
    () => files.reduce((sum, f) => sum + f.size, 0),
    [files]
  );

  const accept = target === "word-to-pdf" ? ".docx" : ".pdf";
  const ocrReady = !!ocrStatus?.tesseract_ok && !!ocrStatus?.poppler_ok;

  useEffect(() => {
    fetch(`${API_BASE}/health/ocr`)
      .then((res) => res.json())
      .then(setOcrStatus)
      .catch(() => setOcrStatus({ tesseract_ok: false, poppler_ok: false }));
  }, []);

  useEffect(() => {
    const storedSession = localStorage.getItem("documind_chat_session");
    const storedMessages = localStorage.getItem("documind_chat_messages");
    if (storedSession) {
      setChatSessionId(storedSession);
    } else {
      const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      setChatSessionId(newId);
      localStorage.setItem("documind_chat_session", newId);
    }

    if (storedMessages) {
      try {
        const parsed = JSON.parse(storedMessages);
        if (Array.isArray(parsed)) {
          setChatMessages(parsed);
          return;
        }
      } catch {}
    }

    setChatMessages([
      { role: "bot", text: "Hi! Ask me anything about your documents. Chat will be enabled once the provider is configured.", ts: Date.now() }
    ]);
  }, []);

  useEffect(() => {
    if (!chatSessionId) return;
    localStorage.setItem("documind_chat_session", chatSessionId);
  }, [chatSessionId]);

  useEffect(() => {
    localStorage.setItem("documind_chat_messages", JSON.stringify(chatMessages));
  }, [chatMessages]);

  useEffect(() => {
    const storedHistory = localStorage.getItem("documind_conversion_history");
    if (storedHistory) {
      try {
        const parsed = JSON.parse(storedHistory);
        if (Array.isArray(parsed)) {
          setConversionHistory(parsed);
        }
      } catch {}
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("documind_conversion_history", JSON.stringify(conversionHistory));
  }, [conversionHistory]);

  function handlePick(e) {
    const list = Array.from(e.target.files || []);
    setFiles(list);
    setMessage("");
  }

  function handleDrop(e) {
    e.preventDefault();
    const list = Array.from(e.dataTransfer.files || []);
    setFiles(list);
    setMessage("");
  }

  function resetFiles() {
    setFiles([]);
    setMessage("");
  }

  async function sendChat() {
    const text = chatInput.trim();
    if (!text || chatBusy) return;
    setChatBusy(true);
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", text, ts: Date.now() }]);

    try {
      const headers = { "Content-Type": "application/json" };
      if (chatSessionId) {
        headers["x-session-id"] = chatSessionId;
      }

      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Chat failed");
      }

      const data = await res.json();
      setChatMessages((prev) => [...prev, { role: "bot", text: data.reply, ts: Date.now() }]);
    } catch (err) {
      setChatMessages((prev) => [...prev, { role: "bot", text: err.message || "Chat error", ts: Date.now() }]);
    } finally {
      setChatBusy(false);
    }
  }

  async function uploadChatDoc(file) {
    if (!file) return;
    setChatDocBusy(true);
    setChatMessages((prev) => [...prev, { role: "bot", text: "Loading document into chat context...", ts: Date.now() }]);

    try {
      const form = new FormData();
      form.append("file", file);

      const headers = {};
      if (chatSessionId) {
        headers["x-session-id"] = chatSessionId;
      }

      const res = await fetch(`${API_BASE}/chat/upload`, {
        method: "POST",
        headers,
        body: form,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Document upload failed");
      }

      const data = await res.json();
      setChatMessages((prev) => [
        ...prev,
        { role: "bot", text: `Document loaded. ${data.chars} characters added to context.`, ts: Date.now() },
      ]);
    } catch (err) {
      setChatMessages((prev) => [...prev, { role: "bot", text: err.message || "Upload error", ts: Date.now() }]);
    } finally {
      setChatDocBusy(false);
    }
  }

  async function summarizeDoc() {
    if (chatSummaryBusy) return;
    setChatSummaryBusy(true);
    setChatMessages((prev) => [...prev, { role: "bot", text: "Generating summary...", ts: Date.now() }]);

    try {
      const headers = {};
      if (chatSessionId) {
        headers["x-session-id"] = chatSessionId;
      }

      const res = await fetch(`${API_BASE}/chat/summary`, {
        method: "POST",
        headers,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Summary failed");
      }

      const data = await res.json();
      setChatMessages((prev) => [...prev, { role: "bot", text: data.reply, ts: Date.now() }]);
    } catch (err) {
      setChatMessages((prev) => [...prev, { role: "bot", text: err.message || "Summary error", ts: Date.now() }]);
    } finally {
      setChatSummaryBusy(false);
    }
  }

  function clearChat() {
    setChatMessages([
      { role: "bot", text: "Chat cleared. Ask me anything.", ts: Date.now() }
    ]);
    localStorage.removeItem("documind_chat_messages");
  }

  function recordConversion(entry) {
    setConversionHistory((prev) => [entry, ...prev].slice(0, 20));
  }

  async function handleConvert() {
    if (!files.length) {
      setMessage("Please add at least one file.");
      return;
    }

    if (totalSize / (1024 * 1024) > SIZE_LIMIT_MB) {
      setMessage(`Total size exceeds ${SIZE_LIMIT_MB} MB limit.`);
      return;
    }

    if (mode === "single" && files.length > 1) {
      setMessage("Switch to Batch mode to convert multiple files.");
      return;
    }

    setBusy(true);
    setMessage("Working locally, hang tight...");
    const entryId = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const entry = {
      id: entryId,
      time: new Date().toLocaleString(),
      target,
      mode,
      files: files.map((f) => f.name),
      status: "processing",
    };
    recordConversion(entry);

    try {
      let url = `${API_BASE}/convert/${target}`;
      const form = new FormData();

      if (mode === "single") {
        form.append("file", files[0]);
      } else {
        url = `${API_BASE}/convert/batch`;
        form.append("target", target);
        files.forEach((f) => form.append("files", f));
      }

      const res = await fetch(url, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Conversion failed");
      }

      const blob = await res.blob();
      const downloadName = res.headers.get("content-disposition")?.split("filename=")?.[1]?.replace(/"/g, "")
        || (mode === "single"
          ? (target === "pdf-to-word" ? "converted.docx" : target === "pdf-to-text" ? "converted.txt" : "converted.pdf")
          : "batch.zip");

      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = downloadName;
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage("Done. File downloaded.");
      setConversionHistory((prev) =>
        prev.map((item) => (item.id === entryId ? { ...item, status: "done" } : item))
      );
    } catch (err) {
      setMessage(err.message || "Something went wrong");
      setConversionHistory((prev) =>
        prev.map((item) => (item.id === entryId ? { ...item, status: "failed" } : item))
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page" onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
      <header className="hero hero-center">
        <div className="hero-left hero-center">
          <h1 className="title-center">DocuMind</h1>
          <p className="tagline title-center">
            Bridge the Gap Between Static Files and Active Intelligence
          </p>
          <p className="quote title-center">
            A local-first document lab for fast conversions and smart assistance.
          </p>
        </div>
        <div className="hero-right hero-right-top">
          <button className="history-button" onClick={() => setHistoryOpen((v) => !v)}>
            <span className="history-icon">⎘</span>
            <span className="history-label">Recent Conversions</span>
          </button>
        </div>
      </header>

      <main className="grid">
        <section className="panel">
          <h2>Conversion</h2>
          <div className="row">
            <button
              className={`pill ${target === "pdf-to-word" ? "active" : ""}`}
              onClick={() => setTarget("pdf-to-word")}
            >
              PDF → Word
            </button>
            <button
              className={`pill ${target === "pdf-to-text" ? "active" : ""} ${ocrReady ? "" : "disabled"}`}
              onClick={() => ocrReady && setTarget("pdf-to-text")}
              disabled={!ocrReady}
            >
              PDF → Text (OCR)
            </button>
            <button
              className={`pill ${target === "word-to-pdf" ? "active" : ""}`}
              onClick={() => setTarget("word-to-pdf")}
            >
              Word → PDF
            </button>
          </div>
          <div className="row">
            <button
              className={`pill ghost ${mode === "single" ? "active" : ""}`}
              onClick={() => setMode("single")}
            >
              Single
            </button>
            <button
              className={`pill ghost ${mode === "batch" ? "active" : ""}`}
              onClick={() => setMode("batch")}
            >
              Batch
            </button>
          </div>
          <div className="meta">
            Accepts {accept} files. Total size: {formatBytes(totalSize)}
          </div>
        </section>

        <section className="panel drop" onDrop={handleDrop}>
          <h2>Drop Files</h2>
          <p className="hint">Drag and drop or pick files below.</p>
          <label className="filepick">
            Choose Files
            <input type="file" accept={accept} multiple onChange={handlePick} />
          </label>
          {files.length > 0 && (
            <div className="filelist">
              {files.map((f) => (
                <div key={`${f.name}-${f.size}`} className="fileitem">
                  <span>{f.name}</span>
                  <span>{formatBytes(f.size)}</span>
                </div>
              ))}
              <button className="link" onClick={resetFiles}>Clear list</button>
            </div>
          )}
        </section>

        <section className="panel action">
          <h2>Run</h2>
          <p className="hint">Processing stays on your machine.</p>
          <button className="cta" onClick={handleConvert} disabled={busy}>
            {busy ? "Converting..." : "Convert Now"}
          </button>
          <div className="status">{message}</div>
          <div className="foot">
            Word → PDF requires Microsoft Word installed locally. PDF → Text uses Tesseract OCR.
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>Phase 1: Conversion core</span>
        <span>Phase 2: OCR and PDF text extraction</span>
        <span>Phase 3: Gemini chat + document memory</span>
      </footer>

      <button className="chat-toggle" onClick={() => setChatOpen((v) => !v)}>
        <span className="chat-orbit"></span>
      </button>

      <aside className={`history-drawer ${historyOpen ? "open" : ""}`}>
        <div className="history-head">
          <h3>Recent Conversions</h3>
          <button className="history-close" onClick={() => setHistoryOpen(false)}>×</button>
        </div>
        {conversionHistory.length === 0 && (
          <div className="hint">No conversions yet.</div>
        )}
        {conversionHistory.length > 0 && (
          <div className="history-list">
            {conversionHistory.map((item) => (
              <div key={item.id} className={`history-item ${item.status}`}>
                <div className="history-top">
                  <span className="history-title">{item.target} • {item.mode}</span>
                  <span className={`history-status ${item.status}`}>{item.status}</span>
                </div>
                <div className="history-meta">
                  <span className="history-chip">{item.files.length} file(s)</span>
                  <span className="history-chip">{item.mode}</span>
                </div>
                <div className="history-files">{item.files.join(", ")}</div>
                <div className="history-time">{item.time}</div>
              </div>
            ))}
          </div>
        )}
      </aside>

      {chatOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <div className="chat-title">DocuMind Chat</div>
            <div className="chat-actions">
              <button className="chat-clear" onClick={clearChat}>Clear</button>
              <button className="chat-close" onClick={() => setChatOpen(false)}>×</button>
            </div>
          </div>
          <div className="chat-body">
            {chatMessages.map((m, i) => (
              <div key={`${m.role}-${i}`} className={`chat-msg ${m.role}`}>
                <div className="chat-text">{m.text}</div>
                {m.ts && <div className="chat-time">{new Date(m.ts).toLocaleTimeString()}</div>}
              </div>
            ))}
          </div>
          <div className="chat-input">
            <input
              type="text"
              placeholder="Ask about a PDF or workflow..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendChat()}
            />
            <button onClick={sendChat} disabled={chatBusy || !chatInput.trim()}>
              {chatBusy ? "..." : "Send"}
            </button>
          </div>
          <div className="chat-doc">
            <label className="chat-doc-btn">
              {chatDocBusy ? "Loading..." : "Attach PDF to Chat"}
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => uploadChatDoc(e.target.files?.[0])}
                disabled={chatDocBusy}
              />
            </label>
            <button className="chat-doc-action" onClick={summarizeDoc} disabled={chatSummaryBusy}>
              {chatSummaryBusy ? "Summarizing..." : "Summarize PDF"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
