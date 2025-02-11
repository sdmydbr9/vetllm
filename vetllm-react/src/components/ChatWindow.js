import React, { useState, useEffect } from 'react';
import ChatHeader from './ChatHeader';
import ChatConversation from './ChatConversation';
import ChatInput from './ChatInput';
import OptionsMenu from './OptionsMenu';

// Initial state: start with category selection and default provider Gemini.
const initialState = {
  conversationState: "selectCategory", // valid: selectCategory, selectAction, multiStepAction, normalChat
  currentMenuState: "category", // "category", "action", etc.
  selectedProvider: "Gemini",
  selectedCategory: null,
  selectedAction: null,
  multiStepAction: null,
  multiStepStep: 0,
  multiStepAnswers: {},
};

const actionsInfo = {
  synonym: { display: "Synonym" },
  diagnostic_workup: { display: "Diagnostic Workup" },
  drug_of_choice: { display: "Drug of Choice" },
  differential_diagnosis: { display: "Differential Diagnosis" },
  line_of_treatment: { display: "Line of Treatment" },
  prognosis: { display: "Prognosis" },
  describe_clinical_signs: { display: "Describe Clinical Signs and Symptoms" },
  symptoms: { display: "Symptoms" },
  reverse_symptom_lookup: { display: "Reverse Symptom Lookup" },
  calculate_dose_rate: { display: "Calculate Dose Rate" },
  indication: { display: "Indication" },
  contraindication: { display: "Contraindication" },
  mechanism_of_action: { display: "Mechanism of Action" },
  metabolism_and_elimination: { display: "Metabolism and Elimination" },
  products: { display: "Products" }
};

const promptInfo = {
  synonym: "Return the disease synonyms for: ",
  diagnostic_workup: "Return the diagnostic workup for: ",
  drug_of_choice: "What is the drug of choice for: ",
  differential_diagnosis: "Return the differential diagnosis for: ",
  line_of_treatment: "Return the line of treatment for: ",
  prognosis: "Return the prognosis for: ",
  describe_clinical_signs: "Describe the clinical signs and symptoms for: ",
  symptoms: "Return the list of matched diseases for the symptoms: ",
  reverse_symptom_lookup: "Return the clinical signs and symptoms for disease: ",
  calculate_dose_rate: "Calculate the dose rate of {ingredient} in a {weight} {species}.",
  indication: "Return the indications for the drug: ",
  contraindication: "Return the contraindications for the drug: ",
  mechanism_of_action: "Return the mechanism of action for the drug {drug}",
  metabolism_and_elimination: "Return the metabolism and elimination details for the drug: ",
  products: "Return the products for the drug: "
};

const menuCategories = {
  "Clinical Data": ["synonym", "diagnostic_workup", "drug_of_choice", "differential_diagnosis", "line_of_treatment", "prognosis"],
  "Disease Symptoms": ["describe_clinical_signs", "symptoms", "reverse_symptom_lookup"],
  "Pharma": ["calculate_dose_rate", "indication", "contraindication", "mechanism_of_action", "metabolism_and_elimination", "products"]
};

function ChatWindow({ onClose }) {
  const [chatState, setChatState] = useState(initialState);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Append a message to the conversation.
  const appendMessage = (sender, text, matches = null, isHTML = false) => {
    setMessages(prev => [...prev, { sender, text, matches, isHTML }]);
  };

  // Recursive helper to format arrays and objects.
  const formatValue = (value) => {
    if (Array.isArray(value)) {
      return value
        .map((item, index) => `${index + 1}. ${formatValue(item)}`)
        .join("\n");
    } else if (typeof value === "object" && value !== null) {
      return Object.keys(value)
        .map(key => `${key.charAt(0).toUpperCase() + key.slice(1)}: ${formatValue(value[key])}`)
        .join("\n");
    } else {
      return value.toString();
    }
  };

  // Format response text (if it is a JSON string) into proper text.
  const formatResponse = (responseText) => {
    try {
      const parsed = JSON.parse(responseText);
      return formatValue(parsed);
    } catch (e) {
      return responseText;
    }
  };

  // When a menu option is selected.
  const handleOptionSelect = (option) => {
    if (chatState.conversationState === "selectCategory") {
      setChatState(prev => ({
        ...prev,
        selectedCategory: option,
        conversationState: "selectAction",
        currentMenuState: "action"
      }));
      // Removed the instructional message.
    } else if (chatState.conversationState === "selectAction") {
      setChatState(prev => ({
        ...prev,
        selectedAction: option
      }));
      // Removed "Action selected" message.
      if (option === "calculate_dose_rate") {
        setChatState(prev => ({
          ...prev,
          conversationState: "multiStepAction",
          multiStepAction: "calculate_dose_rate",
          multiStepStep: 1,
          multiStepAnswers: {}
        }));
        // Retain multi-step prompt so user knows what to enter.
        appendMessage("bot", "Please enter the drug name:");
      } else if (option === "mechanism_of_action") {
        setChatState(prev => ({
          ...prev,
          conversationState: "multiStepAction",
          multiStepAction: "mechanism_of_action",
          multiStepStep: 1,
          multiStepAnswers: {}
        }));
        appendMessage("bot", "Please enter the drug name:");
      } else {
        // For regular actions, switch to normal text input.
        setChatState(prev => ({ ...prev, conversationState: "normalChat" }));
      }
    }
  };

  // Handle the back button in the options menu.
  const handleBack = () => {
    if (chatState.conversationState === "selectAction") {
      setChatState(prev => ({
        ...prev,
        conversationState: "selectCategory",
        currentMenuState: "category",
        selectedCategory: null
      }));
      // Removed the instructional message.
    } else if (chatState.conversationState === "multiStepAction") {
      setChatState(prev => ({
        ...prev,
        conversationState: "selectAction",
        multiStepAction: null,
        multiStepStep: 0,
        multiStepAnswers: {}
      }));
      // Removed the instructional message.
    }
  };

  // Options to display in the current menu.
  const getOptions = () => {
    if (chatState.conversationState === "selectCategory") {
      return Object.keys(menuCategories);
    } else if (chatState.conversationState === "selectAction") {
      const actions = menuCategories[chatState.selectedCategory] || [];
      return actions.map(action => ({ label: actionsInfo[action].display, value: action }));
    }
    return [];
  };

  // Handle user input from the ChatInput component.
  const handleUserInput = async (inputText) => {
    appendMessage("user", inputText);

    // Handle multi-step actions.
    if (chatState.conversationState === "multiStepAction") {
      if (chatState.multiStepAction === "calculate_dose_rate") {
        if (chatState.multiStepStep === 1) {
          setChatState(prev => ({
            ...prev,
            multiStepAnswers: { ...prev.multiStepAnswers, drugname: inputText },
            multiStepStep: 2
          }));
          appendMessage("bot", "Please enter the species:");
          return;
        } else if (chatState.multiStepStep === 2) {
          setChatState(prev => ({
            ...prev,
            multiStepAnswers: { ...prev.multiStepAnswers, species: inputText },
            multiStepStep: 3
          }));
          appendMessage("bot", "Please enter the body weight:");
          return;
        } else if (chatState.multiStepStep === 3) {
          const answers = { ...chatState.multiStepAnswers, bodyweight: inputText };
          const prompt = promptInfo["calculate_dose_rate"]
                          .replace('{ingredient}', answers.drugname)
                          .replace('{weight}', answers.bodyweight)
                          .replace('{species}', answers.species);
          setChatState(prev => ({
            ...prev,
            conversationState: "normalChat",
            multiStepAction: null,
            multiStepStep: 0,
            multiStepAnswers: {}
          }));
          await sendChatRequest(prompt);
          return;
        }
      } else if (chatState.multiStepAction === "mechanism_of_action") {
        if (chatState.multiStepStep === 1) {
          const prompt = promptInfo["mechanism_of_action"].replace('{drug}', inputText.trim());
          setChatState(prev => ({
            ...prev,
            conversationState: "normalChat",
            multiStepAction: null,
            multiStepStep: 0,
            multiStepAnswers: {}
          }));
          await sendChatRequest(prompt);
          return;
        }
      }
    }

    // For normal actions.
    if (chatState.conversationState === "normalChat") {
      await sendChatRequest(inputText);
    }
  };

  // Send the chat request to your API.
  const sendChatRequest = async (message) => {
    setLoading(true);
    let categoryKey = "";
    if (chatState.selectedCategory === "Clinical Data") {
      categoryKey = "clinical";
    } else if (chatState.selectedCategory === "Disease Symptoms") {
      categoryKey = "disease";
    } else if (chatState.selectedCategory === "Pharma") {
      categoryKey = "pharma";
    }
    const endpointURL = categoryKey ? `/${categoryKey}/${chatState.selectedAction}` : '/chat';
    const fullURL = `http://192.168.29.105:7860${endpointURL}`;
    
    try {
      const response = await fetch(fullURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: message, 
          provider: chatState.selectedProvider, 
          endpoint: chatState.selectedAction
        })
      });
      const data = await response.json();
      setLoading(false);
      if (data.error) {
        appendMessage("bot", "Error: " + data.error);
      } else {
        const formattedResponse = formatResponse(data.response);
        const formattedMatches = data.matches ? formatValue(data.matches) : null;
        appendMessage("bot", formattedResponse, formattedMatches, false);
      }
      // After receiving a response, revert to the action selection (without extra prompt messages).
      setChatState(prev => ({ ...prev, conversationState: "selectAction" }));
    } catch (error) {
      setLoading(false);
      appendMessage("bot", "Error: " + error.message);
    }
  };

  // On mount, we no longer append a "Please select a category:" message.
  useEffect(() => {
    // The OptionsMenu will render for category selection.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="chat-window">
      <ChatHeader onClose={onClose} />
      <ChatConversation messages={messages} loading={loading} />
      {getOptions().length > 0 && chatState.conversationState !== "normalChat" ? (
        <OptionsMenu options={getOptions()} onSelect={handleOptionSelect} onBack={handleBack} />
      ) : (
        <ChatInput 
          onSend={handleUserInput} 
          placeholder={
            (chatState.conversationState === "normalChat" && promptInfo[chatState.selectedAction])
              ? promptInfo[chatState.selectedAction]
              : "Type your message here..."
          } 
        />
      )}
    </div>
  );
}

export default ChatWindow;
