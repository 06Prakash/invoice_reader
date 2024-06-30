import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TemplateManager = ({ onTemplateSelect, templates, selectedTemplate, fetchTemplates }) => {
    const [templateName, setTemplateName] = useState('');
    const [templateFields, setTemplateFields] = useState('');

    useEffect(() => {
        if (selectedTemplate) {
            fetchTemplateFields(selectedTemplate);
        }
    }, [selectedTemplate]);

    const handleSaveTemplate = async () => {
        try {
            const fields = JSON.parse(templateFields); // Parse the JSON string to an object
            const template = {
                name: templateName,
                fields
            };

            await axios.post('http://localhost:5001/templates', template);
            setTemplateName('');
            setTemplateFields('');
            fetchTemplates(); // Fetch the updated list of templates
            onTemplateSelect(template.name);
        } catch (error) {
            console.error('Error saving template:', error);
        }
    };

    const fetchTemplateFields = async (templateName) => {
        try {
            const response = await axios.get(`http://localhost:5001/templates/${templateName}`);
            const fields = JSON.stringify(response.data.fields, null, 2); // Convert to pretty JSON
            setTemplateFields(fields);
            setTemplateName(templateName);
        } catch (error) {
            console.error('Error fetching template fields:', error);
        }
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
            <select
                onChange={(e) => onTemplateSelect(e.target.value)}
                value={selectedTemplate}
            >
                <option value="">Select Template</option>
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
