import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import axios from 'axios';
import UploadComponent from './components/UploadComponent';
import DataReview from './components/DataReview';
import RegisterComponent from './components/RegisterComponent';
import LoginComponent from './components/LoginComponent';
import NavBar from './components/NavBar';
import LinearProgress from '@mui/material/LinearProgress';
import PageBasedExtractionComponent from './components/PageBasedExtractionComponent';

import './App.css';

const App = () => {
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [extractedData, setExtractedData] = useState(null);
    const [extractionModels, setExtractionModels] = useState([]);
    const [pageConfig, setPageConfig] = useState({});
    const [selectedModel, setSelectedModel] = useState('NIRA AI - Printed Text (PB)');
    const [originalLines, setOriginalLines] = useState([]);
    const [progress, setProgress] = useState(0);
    const [token, setToken] = useState(localStorage.getItem('jwt_token') || '');

    // Update Axios headers on token change
    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
    }, [token]);

    // Configure Axios Interceptor
    useEffect(() => {
        const axiosInterceptor = axios.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    // Token expired or unauthorized access
                    handleLogout();
                }
                return Promise.reject(error);
            }
        );

        return () => {
            axios.interceptors.response.eject(axiosInterceptor);
        };
    }, []);

    // Simulate progress update
    useEffect(() => {
        if (loading) {
            const interval = setInterval(() => {
                axios
                    .get('/progress')
                    .then((response) => {
                        setProgress(response.data.progress);
                        if (response.data.progress >= 100) {
                            clearInterval(interval);
                        }
                    })
                    .catch((error) => {
                        console.error('Error fetching progress:', error);
                    });
            }, 5000);
            return () => clearInterval(interval);
        }
    }, [loading]);

    // Fetch available extraction models
    useEffect(() => {
        axios.get('/extraction-models')
            .then((response) => {
                setExtractionModels(response.data.models || ['NIRA AI - Printed Text (PB)']); // Fallback to default
            })
            .catch((error) => {
                console.error('Error fetching extraction models:', error);
                setExtractionModels(['NIRA AI - Printed Text (PB)']); // Default on error
            });
    }, []);

    const handleLogout = () => {
        setToken('');
        localStorage.removeItem('jwt_token');
        axios.defaults.headers.common['Authorization'] = null;
    };

    const handlePageConfigSubmit = (config) => {
        setPageConfig(config);
        console.log('Page-based extraction config:', config);
    };

    const handleUploadSuccess = (filenames, extractedData, linesData) => {
        setUploadedFiles(filenames);
        setExtractedData(extractedData);
        setOriginalLines(linesData);
        setMessage('');
    };

    const handleExtractData = () => {
        if (uploadedFiles.length === 0) {
            setMessage('Please upload files and select or generate a template first.');
            return;
        }
        setLoading(true);
        setMessage('');
        setProgress(0);
        const data = {
            filenames: uploadedFiles,
            extraction_model: selectedModel,
            page_config: pageConfig,
        };

        axios
            .post('/extract', data)
            .then((response) => {
                console.log('Data extracted successfully:', response.data);
                setExtractedData(response.data);
                setOriginalLines(response.data.lines_data || {});
                setMessage('Data extracted successfully.');
            })
            .catch((error) => {
                console.error('Error extracting data:', error);
                setMessage('Failed to extract data.');
            })
            .finally(() => {
                setLoading(false);
            });
    };

    const handleExtractionMethodChange = (event) => {
        setSelectedModel(event.target.value);
    };

    return (
        <Router>
            <div className="App">
                <NavBar token={token} setToken={setToken} />
                <Switch>
                    {/* Registration */}
                    <Route
                        path="/register"
                        render={() =>
                            token ? <Redirect to="/" /> : <RegisterComponent setToken={setToken} />
                        }
                    />
                    {/* Login */}
                    <Route
                        path="/login"
                        render={() =>
                            token ? <Redirect to="/" /> : <LoginComponent setToken={setToken} />
                        }
                    />
                    {/* Home */}
                    <Route
                        path="/"
                        render={() =>
                            token ? (
                                <>
                                    <UploadComponent onUploadSuccess={handleUploadSuccess} />
                                    <PageBasedExtractionComponent
                                        onPageExtractionConfigSubmit={handlePageConfigSubmit}
                                        uploadedFiles={uploadedFiles}
                                    />
                                    <div className="output-format-container">
                                        <div className="output-format">
                                            <label htmlFor="extraction-method">
                                                Extraction Method:
                                            </label>
                                            <select
                                                id="extraction-method"
                                                value={selectedModel}
                                                onChange={handleExtractionMethodChange}
                                            >
                                                {extractionModels.map((model) => (
                                                    <option key={model} value={model}>
                                                        {model.charAt(0).toUpperCase() +
                                                            model.slice(1)}{' '}
                                                        Extraction
                                                    </option>
                                                ))}
                                            </select>
                                            <button onClick={handleExtractData} disabled={loading}>
                                                {loading ? `Extracting... ${progress}% completed` : 'Extract Data'}
                                            </button>
                                        </div>
                                    </div>
                                    {message && <p>{message}</p>}
                                    {loading && ( <LinearProgress variant="determinate" value={progress}/> )}
                                    {extractedData && (
                                        <DataReview extractedData={extractedData} originalLines={originalLines} token={token} />
                                    )}
                                </>
                            ) : (
                                <Redirect to="/login" />
                            )
                        }
                    />
                </Switch>
            </div>
        </Router>
    );
};

export default App;
