import React, { useState } from 'react';
import axios from 'axios';
import { Button, CircularProgress, Alert } from '@mui/material';
import { CloudUploadOutlined, DescriptionOutlined } from '@mui/icons-material';
import './styles/UploadComponent.css';

const UploadComponent = ({ onUploadSuccess }) => {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [uploadStatuses, setUploadStatuses] = useState({});
    const [attemptId, setAttemptId] = useState(null);
    const [errorMessage, setErrorMessage] = useState(null);

    const handleFileChange = (e) => {
        setSelectedFiles(Array.from(e.target.files));
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            setErrorMessage('Please select at least one file.');
            return;
        }

        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('files', file));

        setUploading(true);
        setErrorMessage(null);

        try {
            const response = await axios.post('/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    Authorization: `Bearer ${localStorage.getItem("token")}`
                },
            });

            if (response.data.error) {
                setErrorMessage(response.data.error);
                return;
            }

            // Extract attempt ID and file details
            const uploadedFiles = response.data.files;
            setAttemptId(response.data.attempt_id);

            const initialStatuses = uploadedFiles.reduce((acc, file) => {
                acc[file.file_id] = { name: file.file_name, status: "Pending" };
                return acc;
            }, {});

            setUploadStatuses(initialStatuses);
            onUploadSuccess(uploadedFiles.map(f => f.file_name));

            uploadedFiles.forEach(file => trackUploadStatus(file.file_id));

        } catch (error) {
            console.error('Error uploading files:', error);
            setErrorMessage('Failed to upload files. Please try again.');
        } finally {
            setUploading(false);
        }
    };

    const trackUploadStatus = (fileId) => {
        let retries = 0;
        const maxRetries = 5;
        const retryInterval = 5000; // 5 seconds

        const interval = setInterval(async () => {
            try {
                const response = await axios.get(`/status/${fileId}`);
                const newStatus = response.data.status;

                setUploadStatuses(prevStatuses => ({
                    ...prevStatuses,
                    [fileId]: { ...prevStatuses[fileId], status: newStatus }
                }));

                if (newStatus === "Completed" || newStatus === "Failed") {
                    clearInterval(interval);
                }
            } catch (error) {
                console.error(`Error fetching status for file ${fileId}:`, error);
                retries++;

                if (retries >= maxRetries) {
                    clearInterval(interval);
                    setUploadStatuses(prevStatuses => ({
                        ...prevStatuses,
                        [fileId]: { ...prevStatuses[fileId], status: "Error Fetching Status" }
                    }));
                }
            }
        }, retryInterval);
    };

    return (
        <div className="upload-container">
            <div className="file-input-wrapper">
                <label className="custom-file-upload">
                    <CloudUploadOutlined className="upload-icon" />
                    Choose Files
                    <input type="file" multiple onChange={handleFileChange} />
                </label>
                {selectedFiles.length > 0 && (
                    <div className="file-count">
                        <DescriptionOutlined className="file-icon" />
                        {selectedFiles.length} file(s) selected
                    </div>
                )}
            </div>

            {errorMessage && <Alert severity="error" className="upload-error">{errorMessage}</Alert>}

            <Button
                variant="contained"
                className="upload-button"
                onClick={handleUpload}
                disabled={uploading}
                disableElevation
                startIcon={uploading ? <CircularProgress size={18} /> : null}
            >
                {uploading ? 'Uploading...' : 'Upload'}
            </Button>

            {attemptId && <p className="attempt-info">Attempt ID: <strong>{attemptId}</strong></p>}

            {Object.keys(uploadStatuses).length > 0 && (
                <div className="upload-status">
                    <h4>Upload Status</h4>
                    <ul>
                        {Object.values(uploadStatuses).map(({ name, status }) => (
                            <li key={name}>
                                {name}: <strong className={`status-${status.toLowerCase()}`}>{status}</strong>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default UploadComponent;
