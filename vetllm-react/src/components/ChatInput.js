import React, { useState } from 'react';

function ChatInput({ onSend, placeholder }) {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSend(input.trim());
      setInput("");
    }
  };

  return (
    <div className="chat-input-area">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <input 
            type="text" 
            className="form-control" 
            placeholder={placeholder} 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            autoComplete="off"
            required
          />
          <button className="btn btn-primary" type="submit">
            <i className="bi bi-send-fill"></i>
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatInput;
