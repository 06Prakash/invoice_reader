import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UploadComponent from './components/UploadComponent';
import DataReview from './components/DataReview';
import TemplateManager from './components/TemplateManager';
import JsonTemplateGenerator from './components/JsonTemplateGenerator';
import './App.css';

const App = () => {
    const [templates, setTemplates] = useState([]);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [selectedTemplate, setSelectedTemplate] = useState('');
    const [extractedData, setExtractedData] = useState(null);
    const [outputFormat, setOutputFormat] = useState('json');
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [originalLines, setOriginalLines] = useState([]);

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        try {
            const response = await axios.get('http://localhost:5001/templates');
            setTemplates(response.data);
        } catch (error) {
            console.error('Error fetching templates:', error);
        }
    };

    const handleUploadSuccess = (filename) => {
        setUploadedFile(filename);
        setMessage('File uploaded successfully.');
    };

    const handleTemplateGenerated = (generatedTemplate) => {
        fetchTemplates();
        setSelectedTemplate(generatedTemplate.name);
        setMessage('Template generated and saved successfully.');
    };

    const handleTemplateSelect = (templateName) => {
        setSelectedTemplate(templateName);
    };

    const handleExtractData = async () => {
        if (!uploadedFile || !selectedTemplate) {
            setMessage('Please upload a file and select a template first.');
            return;
        }

        setLoading(true);
        setMessage('');

        try {
            const response = await axios.post('http://localhost:5001/extract', {
                filename: uploadedFile,
                template: selectedTemplate,
                output_format: outputFormat
            });

            setExtractedData(response.data.extracted_data || response.data);
            setOriginalLines(response.data.lines_data || []);
            setMessage('Data extracted successfully.');
        } catch (error) {
            console.error('Error extracting data:', error);
            setMessage('Failed to extract data.');
        } finally {
            setLoading(false);
        }
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
            />
            <JsonTemplateGenerator onTemplateGenerated={handleTemplateGenerated} />
            {uploadedFile && (
                <div>
                    <label htmlFor="output-format">Output Format:</label>
                    <select
                        id="output-format"
                        value={outputFormat}
                        onChange={(e) => setOutputFormat(e.target.value)}
                    >
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                        <option value="txt">Text</option>
                    </select>
                    <button onClick={handleExtractData} disabled={loading}>
                        {loading ? 'Extracting...' : 'Extract Data'}
                    </button>
                </div>
            )}
            {message && <p>{message}</p>}
            {extractedData && (
                <DataReview extractedData={extractedData} outputFormat={outputFormat} originalLines={originalLines} />
            )}
        </div>
    );
};

export default App;
