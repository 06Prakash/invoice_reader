import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UploadComponent from './components/UploadComponent';
import DataReview from './components/DataReview';
import TemplateManager from './components/TemplateManager';
import JsonTemplateGenerator from './components/JsonTemplateGenerator';
import './App.css';

const App = () => {
    const [templates, setTemplates] = useState([]);
    const [selectedTemplate, setSelectedTemplate] = useState(null);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [extractedData, setExtractedData] = useState(null);
    const [outputFormat, setOutputFormat] = useState('json');

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = () => {
        axios.get('/templates')
            .then(response => {
                setTemplates(response.data);
            })
            .catch(error => {
                console.error('Error fetching templates:', error);
            });
    };

    const handleTemplateGenerated = (generatedTemplate) => {
        setSelectedTemplate(generatedTemplate.name);
        fetchTemplates();
        setMessage('Template generated and saved successfully.');
    };

    const handleUploadSuccess = (filename) => {
        setUploadedFile(filename);
        setMessage('File uploaded successfully.');
    };

    const handleExtractData = () => {
        if (!uploadedFile || !selectedTemplate) {
            setMessage('Please upload a file and select or generate a template first.');
            return;
        }
        setLoading(true);
        setMessage('');
        const data = {
            filename: uploadedFile,
            template: selectedTemplate,
            output_format: outputFormat
        };

        axios.post('/extract', data)
            .then(response => {
                console.log('Data extracted successfully:', response.data);
                setExtractedData(response.data.extracted_data || response.data);
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

    const isExtractButtonDisabled = !uploadedFile || !selectedTemplate || loading;
    console.log("Is extract button disabled?" + isExtractButtonDisabled)
    return (
        <div className="App">
            <h1>Invoice Extractor</h1>
            <UploadComponent onUploadSuccess={handleUploadSuccess} />
            <TemplateManager templates={templates} onTemplateSelect={handleTemplateSelect} />
            <JsonTemplateGenerator onTemplateGenerated={handleTemplateGenerated} />
            <div>
                <label htmlFor="output-format">Output Format:</label>
                <select id="output-format" value={outputFormat} onChange={handleOutputFormatChange}>
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                    <option value="text">Text</option>
                </select>
            </div>
            <div>
                <button onClick={handleExtractData} disabled={isExtractButtonDisabled}>
                    {loading ? 'Extracting...' : 'Extract Data'}
                </button>
                {message && <p>{message}</p>}
            </div>
            {extractedData && (
                <DataReview extractedData={extractedData} outputFormat={outputFormat} />
            )}
        </div>
    );
};

export default App;
