import React from 'react';

function ChatIcon({ onClick }) {
  return (
    <button className="chat-icon" onClick={onClick} title="Open Chat">
      <i className="bi bi-chat-dots-fill"></i>
    </button>
  );
}

export default ChatIcon;
