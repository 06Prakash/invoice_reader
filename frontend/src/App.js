import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UploadComponent from './components/UploadComponent';
import DataReview from './components/DataReview';
import TemplateManager from './components/TemplateManager';
import JsonTemplateGenerator from './components/JsonTemplateGenerator';
import LinearProgress from '@mui/material/LinearProgress';
import './App.css';

const App = () => {
    const [templates, setTemplates] = useState([]);
    const [selectedTemplate, setSelectedTemplate] = useState('Default Template');
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [extractedData, setExtractedData] = useState(null);
    const [outputFormat, setOutputFormat] = useState('json');
    const [originalLines, setOriginalLines] = useState([]);
    const [defaultTemplateFields, setDefaultTemplateFields] = useState('');

    useEffect(() => {
        fetchTemplates();
        fetchDefaultTemplate();
    }, []);

    const fetchTemplates = () => {
        axios.get('http://localhost:5001/templates')
            .then(response => {
                setTemplates(response.data);
            })
            .catch(error => {
                console.error('Error fetching templates:', error);
            });
    };

    const fetchDefaultTemplate = () => {
        axios.get('http://localhost:5001/default_template')
            .then(response => {
                const fields = JSON.stringify(response.data.fields, null, 2);
                setDefaultTemplateFields(fields);
                if (!templates.includes('Default Template')) {
                    setTemplates(prevTemplates => [...prevTemplates, 'Default Template']);
                }
            })
            .catch(error => {
                console.error('Error fetching default template:', error);
            });
    };

    const handleUploadSuccess = (filenames, extractedData, linesData) => {
        setUploadedFiles(filenames);
        setExtractedData(extractedData);
        setOriginalLines(linesData);
        setMessage('');
    };

    const handleExtractData = () => {
        if (uploadedFiles.length === 0 || !selectedTemplate) {
            setMessage('Please upload files and select or generate a template first.');
            return;
        }
        setLoading(true);
        setMessage('');
        const data = {
            filenames: uploadedFiles,
            template: selectedTemplate,
            output_format: outputFormat
        };

        axios.post('http://localhost:5001/extract', data)
            .then(response => {
                console.log('Data extracted successfully:', response.data);
                setExtractedData(response.data.extracted_data || response.data);
                setOriginalLines(response.data.lines_data || {});
                setMessage('Data extracted successfully.');
            })
            .catch(error => {
                console.error('Error extracting data:', error);
                setMessage('Failed to extract data.');
            })
            .finally(() => {
                setLoading(false);
            });
    };

    const handleTemplateSelect = (templateName) => {
        setSelectedTemplate(templateName);
    };

    const handleOutputFormatChange = (event) => {
        setOutputFormat(event.target.value);
    };

    const handleDownload = (format) => {
        const fileData = extractedData;
        const blob = new Blob([fileData], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `extracted_data.${format}`;
        link.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="App">
            <h1>Invoice Extractor</h1>
            <UploadComponent onUploadSuccess={handleUploadSuccess} />
            <TemplateManager
                templates={templates}
                onTemplateSelect={handleTemplateSelect}
                selectedTemplate={selectedTemplate}
                fetchTemplates={fetchTemplates}
                defaultTemplateFields={defaultTemplateFields}
            />
            <JsonTemplateGenerator onTemplateGenerated={fetchTemplates} />
            <div>
                <label htmlFor="output-format">Output Format:</label>
                <select id="output-format" value={outputFormat} onChange={handleOutputFormatChange}>
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                    <option value="text">Text</option>
                </select>
            </div>
            <div>
                <button onClick={handleExtractData} disabled={loading}>
                    {loading ? 'Extracting...' : 'Extract Data'}
                </button>
                {message && <p>{message}</p>}
            </div>
            {loading && <LinearProgress />}
            {extractedData && (
                <DataReview extractedData={extractedData} outputFormat={outputFormat} originalLines={originalLines} />
            )}
            {extractedData && (
                <div>
                    <button onClick={() => handleDownload(outputFormat)}>Download Data</button>
                </div>
            )}
        </div>
    );
};

export default App;
