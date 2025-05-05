import React, { useState } from 'react';
import axios from 'axios';
import { Button, CircularProgress, LinearProgress } from '@mui/material';
import { CloudUploadOutlined, DescriptionOutlined } from '@mui/icons-material';
import './styles/UploadComponent.css';

const UploadComponent = ({ onUploadSuccess }) => {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [uploadProgress, setUploadProgress] = useState({});
    const [uploadedFiles, setUploadedFiles] = useState([]); // ✅ NEW STATE
    const [uploading, setUploading] = useState(false);

    const handleFileChange = (e) => {
        setSelectedFiles(Array.from(e.target.files));
        setUploadProgress({});
        setUploadedFiles([]);
    };

    const handleUpload = () => {
        if (selectedFiles.length === 0) {
            alert('Please select files first');
            return;
        }

        setUploading(true);

        selectedFiles.forEach((file, index) => {
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                setUploadProgress(prev => ({ ...prev, [file.name]: progress }));

                if (progress >= 100) {
                    clearInterval(interval);
                    setUploadedFiles(prev => [...prev, file.name]); // ✅ MARK AS UPLOADED

                    if (index === selectedFiles.length - 1) {
                        setUploading(false);
                        onUploadSuccess(selectedFiles.map(f => f.name));
                    }
                }
            }, 200);
        });
    };

    return (
        <div className="upload-container">
            <div className="file-input-wrapper">
                <label className="custom-file-upload">
                    <CloudUploadOutlined className="upload-icon" />
                    Choose Files
                    <input type="file" multiple onChange={handleFileChange} />
                </label>
            </div>

            {selectedFiles.length > 0 && (
                <div className="file-list">
                    {selectedFiles.map((file) => (
                        <div key={file.name} className="file-item">
                            <DescriptionOutlined className="file-icon" />
                            <span>{file.name}</span>

                            {uploading && !uploadedFiles.includes(file.name) ? (
                                <LinearProgress
                                    variant="determinate"
                                    value={uploadProgress[file.name] || 0}
                                    className="progress-bar"
                                />
                            ) : uploadedFiles.includes(file.name) ? (
                                <span className="upload-complete">✅ Completed</span>
                            ) : null}
                        </div>
                    ))}
                </div>
            )}

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
        </div>
    );
};

export default UploadComponent;
