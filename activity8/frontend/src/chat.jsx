import React, { useState, useEffect, useRef } from 'react';

export default function ChatApp() {
  // Chat history and session management
  const [sessions, setSessions] = useState([
    { id: '1', title: 'Transcript Analysis Q1', messages: [{ text: "Hello! I loaded your transcript. Ask me anything about it.", sender: 'bot' }] },
    { id: '2', title: 'Python Backend Setup', messages: [{ text: "How can I help with FastAPI?", sender: 'bot' }] }
  ]);
  const [activeSessionId, setActiveSessionId] = useState('1');
  const [input, setInput] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const ws = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Get active session data
  const currentSession = sessions.find(s => s.id === activeSessionId) || sessions[0];

  // Auto-scroll to bottom of chats
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession.messages]);

  // WebSocket Connection Management
  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws/chat');

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
    };

    ws.current.onmessage = (event) => {
      setSessions(prevSessions => prevSessions.map(session => {
        if (session.id === activeSessionId) {
          return {
            ...session,
            messages: [...session.messages, { text: event.data, sender: 'bot' }]
          };
        }
        return session;
      }));
    };

    ws.current.onerror = (event) => {
      console.error('WebSocket error', event);
      setWsConnected(false);
    };

    ws.current.onclose = () => {
      console.log('WebSocket closed');
      setWsConnected(false);
    };

    return () => ws.current?.close();
  }, [activeSessionId]);

  // Handle Text Message Submission
  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      alert('Backend connection is not open. Please check that the server is running.');
      return;
    }

    const updatedMessages = [...currentSession.messages, { text: input, sender: 'user' }];
    
    setSessions(prevSessions => prevSessions.map(session => {
      if (session.id === activeSessionId) {
        const title = session.title.startsWith("New Chat") ? input.substring(0, 24) + "..." : session.title;
        return { ...session, title, messages: updatedMessages };
      }
      return session;
    }));

    ws.current.send(input);
    setInput('');
  };

  // Handle File Upload Pipeline
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      alert('Backend connection is not open. Please start the server before uploading a file.');
      return;
    }

    setIsUploading(true);
    const reader = new FileReader();
    
    reader.onload = (event) => {
      const textContent = event.target.result;

      // 1. Render file upload notification in UI bubble
      const updatedMessages = [
        ...currentSession.messages, 
        { text: `📄 Uploaded file: ${file.name} (${textContent.length} characters)`, sender: 'user' }
      ];

      setSessions(prevSessions => prevSessions.map(session => {
        if (session.id === activeSessionId) {
          return { ...session, messages: updatedMessages };
        }
        return session;
      }));

      // 2. Transmit raw contents via your open WebSocket pipe 
      ws.current.send(textContent);
      setIsUploading(false);
      
      if (fileInputRef.current) {
        fileInputRef.current.value = ''; // Reset input selection
      }
    };

    reader.onerror = () => {
      alert("Failed to read file.");
      setIsUploading(false);
    };

    reader.readAsText(file);
  };

  const createNewChat = () => {
    const newId = String(Date.now());
    const newSession = {
      id: newId,
      title: `New Chat ${sessions.length + 1}`,
      messages: [{ text: "Hello! I am your AI. How can I assist you today?", sender: 'bot' }]
    };
    setSessions([newSession, ...sessions]);
    setActiveSessionId(newId);
  };

  return (
    <div style={styles.appContainer}>
      {/* 1. LEFT SIDEBAR (Chat Histories) */}
      <div style={{ ...styles.sidebar, width: isSidebarOpen ? '260px' : '0px', opacity: isSidebarOpen ? 1 : 0 }}>
        <button onClick={createNewChat} style={styles.newChatBtn}>
          <span style={{ marginRight: '8px' }}>+</span> New chat
        </button>
        <div style={styles.historyList}>
          <p style={styles.historyHeading}>Recent</p>
          {sessions.map(session => (
            <div 
              key={session.id} 
              onClick={() => setActiveSessionId(session.id)}
              style={{
                ...styles.historyItem,
                backgroundColor: session.id === activeSessionId ? '#e8f0fe' : 'transparent',
                color: session.id === activeSessionId ? '#1967d2' : '#3c4043'
              }}
            >
              💬 {session.title}
            </div>
          ))}
        </div>
      </div>

      {/* 2. MAIN CHAT AREA */}
      <div style={styles.mainContent}>
        {/* Top Header */}
        <div style={styles.header}>
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} style={styles.toggleBtn}>
            ☰
          </button>
          <span style={styles.headerTitle}>Gemini Workspace</span>
          <span style={{ ...styles.statusBadge, color: wsConnected ? '#1a73e8' : '#d93025' }}>
            {wsConnected ? 'Connected' : 'Offline'}
          </span>
        </div>

        {/* Message Thread */}
        <div style={styles.chatWindow}>
          <div style={styles.messageList}>
            {currentSession.messages.map((msg, index) => (
              <div 
                key={index} 
                style={{
                  ...styles.messageRow,
                  justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                {msg.sender === 'bot' && <div style={styles.botAvatar}>✦</div>}
                <div style={{
                  ...styles.bubble,
                  backgroundColor: msg.sender === 'user' ? '#e8f0fe' : 'transparent',
                  color: '#1f1f1f',
                  maxWidth: msg.sender === 'user' ? '70%' : '85%'
                }}>
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Bottom Input Area */}
        <div style={styles.inputContainer}>
          <form onSubmit={sendMessage} style={styles.inputForm}>
            {/* Hidden native input file handle */}
            <input 
              type="file" 
              accept=".txt" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              style={{ display: 'none' }} 
            />
            {/* Minimal attachment clip button */}
            <button 
              type="button" 
              onClick={() => fileInputRef.current.click()} 
              style={styles.clipBtn}
              disabled={isUploading}
            >
              📎
            </button>
            <input 
              type="text" 
              value={input} 
              onChange={(e) => setInput(e.target.value)} 
              style={styles.inputField} 
              placeholder={isUploading ? "Uploading content..." : "Message Gemini..."} 
              disabled={isUploading}
            />
            <button type="submit" style={styles.sendBtn} disabled={!input.trim() || isUploading}>
              ➔
            </button>
          </form>
          <p style={styles.disclaimer}>Gemini can make mistakes. Verify important info.</p>
        </div>
      </div>
    </div>
  );
}

// Google AI Inspired Clean Minimalist CSS Styles
const styles = {
  appContainer: { display: 'flex', height: '100vh', backgroundColor: '#f8f9fa', fontFamily: '"Segoe UI", Roboto, sans-serif' },
  sidebar: { backgroundColor: '#f0f4f9', display: 'flex', flexDirection: 'column', padding: '16px 12px', transition: 'all 0.2s ease', overflow: 'hidden', borderRight: '1px solid #e3e3e3' },
  newChatBtn: { display: 'flex', alignItems: 'center', backgroundColor: '#e3e3e3', border: 'none', borderRadius: '24px', padding: '12px 16px', fontSize: '14px', fontWeight: '500', cursor: 'pointer', color: '#444746', marginBottom: '20px', width: 'fit-content' },
  historyList: { flexGrow: 1, overflowY: 'auto' },
  historyHeading: { fontSize: '12px', fontWeight: '600', color: '#444746', paddingLeft: '8px', marginBottom: '8px' },
  historyItem: { padding: '10px 12px', borderRadius: '8px', fontSize: '14px', cursor: 'pointer', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '4px', transition: 'background-color 0.1s' },
  mainContent: { flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#ffffff' },
  header: { height: '56px', display: 'flex', alignItems: 'center', padding: '0 16px', borderBottom: '1px solid #f1f3f4' },
  toggleBtn: { background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', marginRight: '16px', color: '#5f6368' },
  headerTitle: { fontSize: '18px', color: '#1f1f1f', fontWeight: '400' },
  chatWindow: { flexGrow: 1, overflowY: 'auto', display: 'flex', justifyContent: 'center', padding: '20px 16px' },
  messageList: { width: '100%', maxWidth: '720px', display: 'flex', flexDirection: 'column', gap: '24px' },
  messageRow: { display: 'flex', gap: '12px', alignItems: 'flex-start' },
  botAvatar: { width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#e8f0fe', color: '#1a73e8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '16px', flexShrink: 0 },
  bubble: { padding: '8px 16px', borderRadius: '18px', fontSize: '16px', lineHeight: '1.5', whiteSpace: 'pre-wrap', wordBreak: 'break-word' },
  inputContainer: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 16px 16px 16px' },
  inputForm: { width: '100%', maxWidth: '720px', display: 'flex', alignItems: 'center', backgroundColor: '#f0f4f9', borderRadius: '28px', padding: '6px 14px', boxSizing: 'border-box' },
  clipBtn: { background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#5f6368', padding: '0 8px', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  inputField: { flexGrow: 1, border: 'none', background: 'none', height: '40px', outline: 'none', fontSize: '16px', color: '#1f1f1f', paddingLeft: '8px' },
  sendBtn: { background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#1a73e8', padding: '0 8px' },
  statusBadge: { marginLeft: '16px', fontSize: '13px', fontWeight: '600' },
  disclaimer: { fontSize: '12px', color: '#5f6368', marginTop: '8px' }};