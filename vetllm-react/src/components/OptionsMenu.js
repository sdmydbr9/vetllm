import React from 'react';

function OptionsMenu({ options, onSelect, onBack }) {
  return (
    <div className="options-container">
      {options.map((option, index) => {
        const label = typeof option === "object" ? option.label : option;
        const value = typeof option === "object" ? option.value : option;
        return (
          <button key={index} type="button" className="btn btn-outline-secondary" onClick={() => onSelect(value)}>
            {label}
          </button>
        );
      })}
      <button type="button" className="btn btn-secondary" style={{ marginTop: "10px" }} onClick={onBack}>
        Back
      </button>
    </div>
  );
}

export default OptionsMenu;
