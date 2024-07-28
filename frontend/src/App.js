import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UploadComponent from './components/UploadComponent';
import DataReview from './components/DataReview';
import TemplateManager from './components/TemplateManager';
import JsonTemplateGenerator from './components/JsonTemplateGenerator';
import RegisterComponent from './components/RegisterComponent';
import LoginComponent from './components/LoginComponent';
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
    const [progress, setProgress] = useState(0);
    const [token, setToken] = useState(localStorage.getItem('jwt_token') || '');

    // Set the default Authorization header when the app loads
    if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            fetchTemplates();
            fetchDefaultTemplate();
        }
    }, [token]);

    useEffect(() => {
        if (loading) {
            const interval = setInterval(() => {
                axios.get('http://localhost:5001/progress', { headers: { Authorization: `Bearer ${token}` } })
                    .then(response => {
                        setProgress(response.data.progress);
                        if (response.data.progress >= 100) {
                            clearInterval(interval);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching progress:', error);
                    });
            }, 5000);
            return () => clearInterval(interval);
        }
    }, [loading, token]);

    const fetchTemplates = () => {
        axios.get('http://localhost:5001/templates', { headers: { Authorization: `Bearer ${token}` } })
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
                alert('Error fetching default template');
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
        setProgress(0);
        const data = {
            filenames: uploadedFiles,
            template: selectedTemplate,
            output_format: outputFormat
        };

        axios.post('http://localhost:5001/extract', data, { headers: { Authorization: `Bearer ${token}` } })
            .then(response => {
                console.log('Data extracted successfully:', response.data);
                setExtractedData(response.data);
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

    const handleLogout = () => {
        setToken('');
        localStorage.removeItem('jwt_token');
        delete axios.defaults.headers.common['Authorization'];
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

    const handleTemplateGenerated = (templateName) => {
        fetchTemplates();
        setSelectedTemplate(templateName);
    };

    return (
        <div className="App">
            {!token ? (
                <div>
                    <RegisterComponent />
                    <LoginComponent setToken={(token) => {
                        setToken(token);
                        localStorage.setItem('jwt_token', token);
                        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
                    }} />
                </div>
            ) : (
                <div>
                    <button onClick={handleLogout}>Logout</button>
                    <h1>Invoice Extractor</h1>
                    <UploadComponent onUploadSuccess={handleUploadSuccess} />
                    <TemplateManager
                        templates={templates}
                        onTemplateSelect={handleTemplateSelect}
                        selectedTemplate={selectedTemplate}
                        fetchTemplates={fetchTemplates}
                        defaultTemplateFields={defaultTemplateFields}
                    />
                    <JsonTemplateGenerator onTemplateGenerated={handleTemplateGenerated} fetchTemplates={fetchTemplates} />
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
                            {loading ? `Extracting... ${progress}% completed` : 'Extract Data'}
                        </button>
                        {message && <p>{message}</p>}
                    </div>
                    {loading && <LinearProgress variant="determinate" value={progress} />}
                    {extractedData && (
                        <DataReview extractedData={extractedData} outputFormat={outputFormat} originalLines={originalLines} />
                    )}
                    {extractedData && (
                        <div>
                            <button onClick={() => handleDownload(outputFormat)}>Download Data</button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default App;