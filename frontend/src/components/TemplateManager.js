import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TemplateManager = ({ templates, onTemplateSelect }) => {
    const [templateName, setTemplateName] = useState('');
    const [templateFields, setTemplateFields] = useState('');

    useEffect(() => {
        if (templates.length > 0) {
            const initialTemplate = templates[0];
            setTemplateName(initialTemplate);
            loadTemplate(initialTemplate);
        }
    }, [templates]);

    const handleSaveTemplate = async () => {
        const template = {
            name: templateName,
            fields: JSON.parse(templateFields)
        };

        try {
            const response = await axios.post('/templates', template);
            alert(response.data.message);
            onTemplateSelect(template.name);
        } catch (error) {
            console.error('Error saving template:', error);
        }
    };

    const loadTemplate = async (name) => {
        const response = await axios.get(`/templates/${name}`);
        setTemplateFields(JSON.stringify(response.data.fields, null, 2));
        setTemplateName(name);
        onTemplateSelect(name);
    };

    return (
        <div>
            <h2>Template Management</h2>
            <input
                type="text"
                placeholder="Template Name"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
            />
            <textarea
                placeholder='Enter fields in JSON format. Example: [{"name": "VAT REG NO", "keyword": "VAT REG NO", "separator": ":", "index": 1}]'
                value={templateFields}
                onChange={(e) => setTemplateFields(e.target.value)}
            ></textarea>
            <button onClick={handleSaveTemplate}>Save Template</button>
            <select value={templateName} onChange={(e) => loadTemplate(e.target.value)}>
                {templates.map((template) => (
                    <option key={template} value={template}>
                        {template}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default TemplateManager;
