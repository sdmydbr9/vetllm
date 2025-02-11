import React, { useState } from 'react';

function ChatHeader({ onClose }) {
  const [isFullScreen, setFullScreen] = useState(false);

  const toggleFullScreen = () => {
    setFullScreen(!isFullScreen);
    // Toggle the "fullscreen" class on the chat window.
    const chatWindow = document.querySelector('.chat-window');
    if (chatWindow) {
      chatWindow.classList.toggle('fullscreen', !isFullScreen);
    }
  };

  return (
    <div className="chat-header">
      <span className="chat-title">
        <i className="bi bi-chat-dots-fill"></i> VetLLM Chat
      </span>
      <div className="chat-header-buttons">
        <button className="btn btn-sm btn-secondary" onClick={toggleFullScreen} title="Full Screen">
          <i className={`bi ${isFullScreen ? 'bi-fullscreen-exit' : 'bi-arrows-fullscreen'}`}></i>
        </button>
        <button className="btn btn-sm btn-danger" onClick={onClose} title="Close Chat">
          <i className="bi bi-x"></i>
        </button>
      </div>
    </div>
  );
}

export default ChatHeader;

