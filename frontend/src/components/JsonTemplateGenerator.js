import React, { useState } from 'react';
import axios from 'axios';
import { Accordion, AccordionSummary, AccordionDetails, TextField, Button, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import './JsonTemplateGenerator.css';

const JsonTemplateGenerator = ({ fetchTemplates }) => {
    const [templateName, setTemplateName] = useState('');
    const [headings, setHeadings] = useState('');

    const handleGenerateTemplate = async () => {
        if (!templateName || !headings.trim()) {
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
        } catch (error) {
            console.error('Error generating template:', error);
        }
    };

    return (
        <div className="json-template-generator">
            <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Generate JSON Template</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <div className="form-group">
                        <TextField
                            label="Template Name"
                            value={templateName}
                            onChange={(e) => setTemplateName(e.target.value)}
                            fullWidth
                            margin="normal"
                        />
                        <TextField
                            label="Headings"
                            value={headings}
                            onChange={(e) => setHeadings(e.target.value)}
                            fullWidth
                            margin="normal"
                            multiline
                            rows={4}
                            placeholder="Enter headings, separated by commas"
                        />
                        <Button
                            variant="contained"
                            className="generate-button"
                            onClick={handleGenerateTemplate}
                        >
                            Generate Template
                        </Button>
                    </div>
                </AccordionDetails>
            </Accordion>
        </div>
    );
};

export default JsonTemplateGenerator;
