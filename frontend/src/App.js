// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import axios from 'axios';
import UploadComponent from './components/UploadComponent';
import DataReview from './components/DataReview';
import TemplateManager from './components/TemplateManager';
import JsonTemplateGenerator from './components/JsonTemplateGenerator';
import RegisterComponent from './components/RegisterComponent';
import LoginComponent from './components/LoginComponent';
import NavBar from './components/NavBar';
import LinearProgress from '@mui/material/LinearProgress';
import './App.css';
import './components/JsonTemplateGenerator.css'; // Include the new CSS file

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
                axios.get('/progress')
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
    }, [loading]);

    const fetchTemplates = () => {
        axios.get('/templates')
            .then(response => {
                setTemplates(response.data);
            })
            .catch(error => {
                console.error('Error fetching templates:', error);
            });
    };

    const fetchDefaultTemplate = () => {
        axios.get('/default_template')
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
        setProgress(0);
        const data = {
            filenames: uploadedFiles,
            template: selectedTemplate,
            output_format: outputFormat
        };

        axios.post('/extract', data)
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
        <Router>
            <div className="App">
                <NavBar token={token} setToken={setToken} />
                <Switch>
                    <Route path="/register">
                        {token ? <Redirect to="/" /> : <RegisterComponent setToken={setToken} />}
                    </Route>
                    <Route path="/login">
                        {token ? <Redirect to="/" /> : <LoginComponent setToken={setToken} />}
                    </Route>
                    <Route path="/">
                        {!token ? (
                            <Redirect to="/login" />
                        ) : (
                            <div>
                                <UploadComponent onUploadSuccess={handleUploadSuccess} />
                                <TemplateManager
                                    templates={templates}
                                    onTemplateSelect={handleTemplateSelect}
                                    selectedTemplate={selectedTemplate}
                                    fetchTemplates={fetchTemplates}
                                    defaultTemplateFields={defaultTemplateFields}
                                />
                                <JsonTemplateGenerator fetchTemplates={fetchTemplates} />
                                <div className="output-format-container">
                                    <div className="output-format">
                                        <label htmlFor="output-format">Output Format:</label>
                                        <select id="output-format" value={outputFormat} onChange={handleOutputFormatChange}>
                                            <option value="json">JSON</option>
                                            <option value="csv">CSV</option>
                                            <option value="text">Text</option>
                                        </select>
                                        <button onClick={handleExtractData} disabled={loading}>
                                            {loading ? `Extracting... ${progress}% completed` : 'Extract Data'}
                                        </button>
                                    </div>
                                </div>

                                {message && <p>{message}</p>}
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
                    </Route>
                </Switch>
            </div>
        </Router>
    );
};

export default App;
