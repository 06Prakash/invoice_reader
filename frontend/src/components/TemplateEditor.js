import React, { useState } from 'react';
import './TemplateEditor.css'; // Make sure to create this CSS file

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
            <div className="form-group">
                <label htmlFor="title">Title:</label>
                <input
                    type="text"
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                />
            </div>
            <div className="form-group">
                <label htmlFor="separator">Separator:</label>
                <input
                    type="text"
                    id="separator"
                    value={separator}
                    onChange={(e) => setSeparator(e.target.value)}
                />
            </div>
            <div className="form-group">
                <label htmlFor="boundaryLeft">Boundary Left:</label>
                <input
                    type="text"
                    id="boundaryLeft"
                    value={boundaryLeft}
                    onChange={(e) => setBoundaryLeft(e.target.value)}
                />
            </div>
            <div className="form-group">
                <label htmlFor="boundaryRight">Boundary Right:</label>
                <input
                    type="text"
                    id="boundaryRight"
                    value={boundaryRight}
                    onChange={(e) => setBoundaryRight(e.target.value)}
                />
            </div>
            <button className="save-button" onClick={handleSave}>Save Template</button>
        </div>
    );
};

export default TemplateEditor;
