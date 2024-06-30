import React, { useState } from 'react';
import axios from 'axios';

const JsonTemplateGenerator = ({ onTemplateGenerated }) => {
    const [templateName, setTemplateName] = useState('');
    const [headings, setHeadings] = useState('');

    const handleGenerateTemplate = async () => {
        const headingsArray = headings.split(',').map(h => h.trim());
        const fields = headingsArray.map(heading => ({
            name: heading,
            keyword: heading,
            separator: ':',
            index: 1
        }));

        const template = {
            name: templateName,
            fields
        };

        try {
            const response = await axios.post('/templates', template);
            alert(response.data.message);
            onTemplateGenerated(template); // Notify parent component about the new template
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
            <input
                type="text"
                placeholder="Enter headings, separated by commas"
                value={headings}
                onChange={(e) => setHeadings(e.target.value)}
            />
            <button onClick={handleGenerateTemplate}>Generate Template</button>
        </div>
    );
};

export default JsonTemplateGenerator;
