import React, { useState } from 'react';
import ChatIcon from './components/ChatIcon';
import ChatWindow from './components/ChatWindow';

function App() {
  const [isChatOpen, setChatOpen] = useState(false);

  const toggleChatWindow = () => {
    setChatOpen(!isChatOpen);
  };

  return (
    <div className="App">
      {!isChatOpen && <ChatIcon onClick={toggleChatWindow} />}
      {isChatOpen && <ChatWindow onClose={toggleChatWindow} />}
    </div>
  );
}

export default App;
