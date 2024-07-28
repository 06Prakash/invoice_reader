import React from 'react';

const OriginalLinesDisplay = ({ lines, onSelect }) => {
    return (
        <div className="original-lines">
            <h3>Original Lines</h3>
            {lines.map((line, index) => (
                <div key={index} onClick={() => onSelect(line)}>
                    {line}
                </div>
            ))}
        </div>
    );
};

export default OriginalLinesDisplay;
