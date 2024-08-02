import React, { useState } from 'react';
import axios from 'axios';
import './JsonTemplateGenerator.css';

const JsonTemplateGenerator = ({ onTemplateGenerated, fetchTemplates }) => {
    const [templateName, setTemplateName] = useState('');
    const [headings, setHeadings] = useState('');

    const handleGenerateTemplate = async () => {
        if (!templateName || !headings) {
            alert('Please enter both template name and headings.');
            return;
        }

        const fields = headings.split(',').map((heading) => ({
            name: heading.trim(),
            keyword: heading.trim(),
            separator: ':',
            index: '1',
            boundaries: {
                left: '',
                right: '',
                up: '',
                down: ''
            },
            data_type: 'text'
        }));

        const template = {
            name: templateName,
            fields: fields
        };

        try {
            await axios.post('http://localhost:5001/templates', template);
            alert('Template generated and saved successfully.');
            fetchTemplates(); // Fetch the updated list of templates
            onTemplateGenerated(template.name);
        } catch (error) {
            console.error('Error generating template:', error);
        }
    };

    return (
        <div className="json-template-generator">
            <h2>Generate JSON Template</h2>
            <div className="form-group">
                <label>Template Name</label>
                <input
                    type="text"
                    placeholder="Enter template name"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                />
            </div>
            <div className="form-group">
                <label>Headings</label>
                <textarea
                    placeholder="Enter headings, separated by commas"
                    value={headings}
                    onChange={(e) => setHeadings(e.target.value)}
                ></textarea>
            </div>
            <button onClick={handleGenerateTemplate}>Generate Template</button>
        </div>
    );
};

export default JsonTemplateGenerator;
