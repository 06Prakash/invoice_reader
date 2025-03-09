import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import axios from 'axios';
import './components/styles/global_stylings.css';
import UploadComponent from './components/UploadComponent';
import DataReview from './components/DataReview';
import RegisterComponent from './components/RegisterComponent';
import LoginComponent from './components/LoginComponent';
import PaymentPageComponent from "./components/PaymentPageComponent";
import NavBar from './components/NavBar';
import LinearProgress from '@mui/material/LinearProgress';
import PageBasedExtractionComponent from './components/PageBasedExtractionComponent';
import CreditUpdateComponent from './components/CreditUpdateComponent';
import CompanyRegisterComponent from './components/CompanyRegisterComponent';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/node/AlertTitle';
import './App.css';

const App = () => {
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const [snackbarType, setSnackbarType] = useState('success');
    const [extractedData, setExtractedData] = useState(null);
    const [extractionModels, setExtractionModels] = useState([]);
    const [pageConfig, setPageConfig] = useState({});
    const [selectedModel, setSelectedModel] = useState('NIRA AI - Printed Text (PB)');
    const [originalLines, setOriginalLines] = useState([]);
    const [progress, setProgress] = useState(0);
    const [token, setToken] = useState(localStorage.getItem('jwt_token') || '');
    const [userRole, setUserRole] = useState(
        localStorage.getItem('special_admin') === 'true' ? 'special_admin' : 'user'
    );
    const [failedFiles, setFailedFiles] = useState([]);
    const MAX_FILES = 5;

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
                } else if (error.response?.status === 400 && error.response?.data?.message) {
                    // Show toast for credit-related issues
                    showToast(error.response.data.message, 'error');
                }
                return Promise.reject(error);
            }
        );

        return () => {
            axios.interceptors.response.eject(axiosInterceptor);
        };
    }, []);

    // Show a toast/snackbar
    const showToast = (msg, type) => {
        setMessage(msg);
        setSnackbarType(type);
        setSnackbarOpen(true);
    };

    // Close the snackbar
    const handleSnackbarClose = () => {
        setSnackbarOpen(false);
    };

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

    useEffect(() => {
        const refreshTokenInterval = setInterval(async () => {
            try {
                const refreshResponse = await axios.post('/user/refresh-token', null, {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem('refresh_token')}`,
                    },
                });
    
                const { access_token } = refreshResponse.data;
    
                // Update the token in localStorage and Axios headers
                localStorage.setItem('jwt_token', access_token);
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                console.log('Token refreshed successfully.');
            } catch (error) {
                console.error('Failed to refresh token:', error);
                handleLogout(); // Logout user if token refresh fails
            }
        }, 2 * 60 * 1000); // Refresh every 2 minutes
    
        return () => clearInterval(refreshTokenInterval); // Cleanup on unmount
    }, []);

    const handleLogout = () => {
        setToken('');
        setUserRole('user');
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('special_admin');
        axios.defaults.headers.common['Authorization'] = null;
    };

    const handlePageConfigSubmit = (config) => {
        setPageConfig(config);
        console.log('Page-based extraction config:', config);
    };

    const handleUploadSuccess = (filenames, extractedData, linesData) => {
        if (filenames.length > MAX_FILES) {
            showToast(`You can upload a maximum of ${MAX_FILES} files.`, 'error');
            return;
        }
        setUploadedFiles(filenames);
        setExtractedData(extractedData);
        setOriginalLines(linesData);
        setMessage('');
    };

    const handleExtractData = () => {
        if (uploadedFiles.length === 0) {
            setMessage('Please upload files first.');
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
                // Check for failed files in response
                if (response.data.failed_files && response.data.failed_files.length > 0) {
                    setFailedFiles(response.data.failed_files);
                } 
                showToast('Data extracted successfully.', 'success');
                setMessage('Data extracted successfully.');
            })
            .catch((error) => {
                console.error('Error extracting data:', error);
                const errorMessage = error.response?.data?.message || 'An unexpected error occurred.';
                setMessage(errorMessage);
            })
            .finally(() => {
                setLoading(false);
            });
    };

    const handleExtractionMethodChange = (event) => {
        setSelectedModel(event.target.value);
    };

    const ProtectedRoute = ({ component: Component, token, userRole, ...rest }) => (
        <Route
            {...rest}
            render={(props) =>
                token && userRole === 'special_admin' ? (
                    <Component {...props} />
                ) : (
                    <Redirect to="/" />
                )
            }
        />
    );    

    return (
        <Router>
            <div className="App" key={userRole}>
            <NavBar token={token} setToken={setToken} userRole={userRole} setUserRole={setUserRole} />
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
                            token ? <Redirect to="/" /> : <LoginComponent setToken={setToken} setUserRole={setUserRole} />
                        }
                    />
                    <ProtectedRoute path="/credit-update" component={CreditUpdateComponent} token={token} userRole={userRole} />
                    <Route
                        path="/payment"
                        render={() =>
                            token ? (
                            <PaymentPageComponent userId={123 /* Pass logged-in user ID dynamically */} />
                            ) : (
                            <Redirect to="/login" />
                            )
                        }
                    />
                    <ProtectedRoute path="/company-register" component={CompanyRegisterComponent} token={token} userRole={userRole} />

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

                                    {Object.keys(failedFiles).length > 0 && (
                                        <div className="error-container">
                                            <Alert severity="error">
                                                <AlertTitle>Extraction Failed for Some Files</AlertTitle>
                                                {Object.entries(failedFiles).map(([file, error]) => (
                                                    <div key={file}><strong>{file}:</strong> {error}</div>
                                                ))}
                                            </Alert>
                                        </div>
                                    )}
                                    {extractedData && (
                                        <DataReview extractedData={extractedData} originalLines={originalLines} token={token} />
                                    )}
                                </>
                            ) : (
                                <Redirect to="/login" />
                            )
                        }
                    />
                   <Route path="*">
                        <div>
                            <h1>404: Route Not Found</h1>
                            <p>Current URL: {window.location.pathname}</p>
                        </div>
                    </Route>
                </Switch>

                {/* Snackbar for notifications */}
                <Snackbar
                    open={snackbarOpen}
                    autoHideDuration={5000}
                    onClose={handleSnackbarClose}
                    anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                >
                    <Alert onClose={handleSnackbarClose} severity={snackbarType}>
                        {message}
                    </Alert>
                </Snackbar>
            </div>
        </Router>
    );
};

export default App;
