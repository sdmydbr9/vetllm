import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';

function ChatConversation({ messages, loading }) {
  const conversationRef = useRef(null);

  useEffect(() => {
    if (conversationRef.current) {
      conversationRef.current.scrollTop = conversationRef.current.scrollHeight;
    }
  }, [messages, loading]);

  return (
    <div id="conversation" className="chat-body" ref={conversationRef}>
      {messages.map((msg, index) => (
        <ChatMessage key={index} sender={msg.sender} text={msg.text} matches={msg.matches} isHTML={msg.isHTML} />
      ))}
      {loading && (
        <div className="message bot">
          <div className="bubble loading-bubble">
            <span className="loading-dot"></span>
            <span className="loading-dot"></span>
            <span className="loading-dot"></span>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatConversation;
