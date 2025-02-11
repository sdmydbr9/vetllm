import React from 'react';

function ChatMessage({ sender, text, matches, isHTML }) {
  const toggleReference = (e) => {
    e.preventDefault();
    const refElem = e.currentTarget.nextSibling;
    if (refElem) {
      refElem.style.display = refElem.style.display === "block" ? "none" : "block";
    }
  };

  return (
    <div className={`message ${sender}`}>
      <div className="bubble fade-in">
        {isHTML ? (
          <span dangerouslySetInnerHTML={{ __html: text }} />
        ) : (
          <span>{text}</span>
        )}
        {sender === "bot" && matches && (
          <>
            <a href="#" className="reference-link" onClick={toggleReference}>
              Reference
            </a>
            <div className="hidden-reference" style={{ display: "none" }}>
              {matches}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
