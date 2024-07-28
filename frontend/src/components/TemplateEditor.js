import React, { useState } from 'react';

const TemplateEditor = ({ onSave }) => {
    const [title, setTitle] = useState('');
    const [separator, setSeparator] = useState(':');
    const [boundaryLeft, setBoundaryLeft] = useState('');
    const [boundaryRight, setBoundaryRight] = useState('');

    const handleSave = () => {
        const field = {
            name: title,
            keyword: title,
            separator,
            boundary_left: boundaryLeft,
            boundary_right: boundaryRight
        };
        onSave(field);
    };

    return (
        <div className="template-editor">
            <h3>Create/Edit Template</h3>
            <div>
                <label>Title:</label>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div>
                <label>Separator:</label>
                <input type="text" value={separator} onChange={(e) => setSeparator(e.target.value)} />
            </div>
            <div>
                <label>Boundary Left:</label>
                <input type="text" value={boundaryLeft} onChange={(e) => setBoundaryLeft(e.target.value)} />
            </div>
            <div>
                <label>Boundary Right:</label>
                <input type="text" value={boundaryRight} onChange={(e) => setBoundaryRight(e.target.value)} />
            </div>
            <button onClick={handleSave}>Save Template</button>
        </div>
    );
};

export default TemplateEditor;
