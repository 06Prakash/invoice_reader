import React, { useState } from 'react';
import axios from 'axios';

const JsonTemplateGenerator = ({ onTemplateGenerated, fetchTemplates }) => {
    const [templateName, setTemplateName] = useState('');
    const [headings, setHeadings] = useState('');

    const handleGenerateTemplate = async () => {
        if (!templateName || !headings && templateName.trim() !== "" && headings.trim() !== "") {
            alert('Please enter both template name and headings.');
            return;
        }

        const fields = headings.split(',').map((heading, index) => ({
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
        <div>
            <h2>Generate JSON Template</h2>
            <input
                type="text"
                placeholder="Enter template name"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
            />
            <textarea
                placeholder="Enter headings, separated by commas"
                value={headings}
                onChange={(e) => setHeadings(e.target.value)}
            ></textarea>
            <button onClick={handleGenerateTemplate}>Generate Template</button>
        </div>
    );
};

export default JsonTemplateGenerator;
