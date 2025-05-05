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
    // State variables
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [extractedData, setExtractedData] = useState(null);
    const [originalLines, setOriginalLines] = useState({});
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [selectedModel, setSelectedModel] = useState('NIRA AI - Printed Text (PB)');
    const [pageConfig, setPageConfig] = useState({});

    // Mock extraction models
    const extractionModels = [
        'NIRA AI - Printed Text (PB)',
        'NIRA AI - Handwritten Text (HW)',
        'Standard OCR'
    ];

    // Mock upload success handler
    const handleUploadSuccess = (filenames) => {
        setUploadedFiles(filenames);
    };

    // Mock extract data function
    const handleExtractData = () => {
        setLoading(true);
        setProgress(0);
        
        // Simulate extraction progress
        const interval = setInterval(() => {
            setProgress(prev => {
                const newProgress = prev + 10;
                if (newProgress >= 100) {
                    clearInterval(interval);
                    setLoading(false);
                    
                    // Create mock extracted data
                    const mockData = {
                        json_data: {
                            'file1.pdf': '/downloads/file1.json',
                            'file2.pdf': '/downloads/file2.json'
                        },
                        excel_paths: {
                            'file1.pdf': '/downloads/file1.xlsx',
                            'file2.pdf': '/downloads/file2.xlsx'
                        },
                        combined_excel_paths: {
                            'combined': '/downloads/combined.xlsx'
                        },
                        lines_data: {
                            'file1.pdf': "This is sample text from file1.pdf\nLine 2 content\nLine 3 content",
                            'file2.pdf': "File2 content line1\nLine2 content here"
                        }
                    };
                    
                    setExtractedData(mockData);
                    setOriginalLines(mockData.lines_data);
                    return 100;
                }
                return newProgress;
            });
        }, 500);
    };

    return (
        <div className="App">
            <UploadComponent onUploadSuccess={handleUploadSuccess} />
            <PageBasedExtractionComponent
                onPageExtractionConfigSubmit={setPageConfig}
                uploadedFiles={uploadedFiles}
            />
            
            <div className="output-format-container">
                <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                >
                    {extractionModels.map(model => (
                        <option key={model} value={model}>{model}</option>
                    ))}
                </select>
                <button onClick={handleExtractData} disabled={loading}>
                    {loading ? `Extracting... ${progress}%` : 'Extract Data'}
                </button>
            </div>

            {extractedData && (
                <DataReview 
                    extractedData={extractedData} 
                    originalLines={originalLines} 
                />
            )}
        </div>
    );
};

export default App;