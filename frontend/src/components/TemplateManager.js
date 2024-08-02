import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TemplateManager.css';

const TemplateManager = ({ onTemplateSelect, templates, selectedTemplate, fetchTemplates }) => {
    const [templateName, setTemplateName] = useState('');
    const [templateFields, setTemplateFields] = useState('');
    
    useEffect(() => {
        fetchDefaultTemplate();
    }, []);

    useEffect(() => {
        if (selectedTemplate) {
            fetchTemplateFields(selectedTemplate);
        }
    }, [selectedTemplate]);

    const handleSaveTemplate = async () => {
        let fields;
        try {
            fields = JSON.parse(templateFields);
        } catch (error) {
            alert('Invalid JSON format in template fields.');
            return;
        }

        const template = {
            name: templateName,
            fields: fields.map(field => ({
                name: field.name.trim(),
                keyword: field.keyword.trim(),
                separator: field.separator || ':',
                boundaries: field.boundaries || { left: '', right: '' },
                data_type: field.data_type || 'text',
                index: field.index || '1'
            }))
        };

        try {
            await axios.post('/templates', template);
            setTemplateName('');
            setTemplateFields('');
            fetchTemplates();
            onTemplateSelect(template.name);
            fetchTemplateFields(template.name); // Fetch the updated template fields
        } catch (error) {
            console.error('Error saving template:', error);
        }
    };

    const fetchTemplateFields = async (templateName) => {
        try {
            if (templateName === 'Default Template') {
                templateName = 'default_template';
                const response = await axios.get(`/default_template`);
                const fields = JSON.stringify(response.data.fields, null, 2);
                setTemplateFields(fields);
                setTemplateName(templateName);
            } else {
                const response = await axios.get(`/templates/${templateName}`);
                const fields = JSON.stringify(response.data.fields, null, 2);
                setTemplateFields(fields);
                setTemplateName(templateName);
            }
        } catch (error) {
            console.error('Error fetching template fields:', error);
        }
    };

    const fetchDefaultTemplate = async () => {
        try {
            const response = await axios.get('/templates/default');
            const fields = JSON.stringify(response.data.fields, null, 2);
            setTemplateFields(fields);
            setTemplateName('Default Template');
            onTemplateSelect('Default Template');
        } catch (error) {
            console.error('Error fetching default template:', error);
        }
    };

    return (
        <div className="template-manager">
            <h2>Template Management</h2>
            <div className="form-group">
                <label>Template Name</label>
                <input
                    type="text"
                    placeholder="Template Name"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                />
            </div>
            <div className="form-group">
                <label>Template Fields</label>
                <textarea
                    placeholder='Enter fields in JSON format. Example: [{"name": "VAT REG NO", "keyword": "VAT REG NO", "separator": ":", "index": 1}]'
                    value={templateFields}
                    onChange={(e) => setTemplateFields(e.target.value)}
                ></textarea>
            </div>
            <button onClick={handleSaveTemplate}>Save Template</button>
            <div className="select-template-group">
                <label>Select Template</label>
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
        </div>
    );
};

export default TemplateManager;
