import React, { useState } from 'react';
import axios from 'axios';
import { Button, CircularProgress, LinearProgress } from '@mui/material';
import { CloudUploadOutlined, DescriptionOutlined } from '@mui/icons-material';
import './styles/UploadComponent.css';

const UploadComponent = ({ onUploadSuccess }) => {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [uploadProgress, setUploadProgress] = useState({}); // Track file progress
    const [uploading, setUploading] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState([]);

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(files);
        setUploadProgress({}); // Reset progress
        setUploadedFiles([]);  // Reset completed uploads
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            alert('Please select files first');
            return;
        }
    
        setUploading(true);
        let uploadedFileNames = [];
        const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB chunks
    
        for (let file of selectedFiles) {
            let start = 0;
            let chunkIndex = 0;
            const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
            const sanitizedFilename = file.name.replace(/\s+/g, '_'); // Replace spaces with underscores
    
            while (start < file.size) {
                const chunk = file.slice(start, start + CHUNK_SIZE);
                const formData = new FormData();
                formData.append('file', chunk, sanitizedFilename);
                formData.append('filename', sanitizedFilename);
                formData.append('chunkIndex', chunkIndex);
                formData.append('totalChunks', totalChunks);
    
                // ✅ Store chunkIndex in a local variable to avoid unsafe closure
                const currentChunkIndex = chunkIndex;
    
                try {
                    const response = await axios.post('/upload_chunk', formData, {
                        headers: { 'Content-Type': 'multipart/form-data' },
                        onUploadProgress: (progressEvent) => {
                            // ✅ Use the stored chunk index
                            const percentCompleted = Math.round((currentChunkIndex / totalChunks) * 100);
                            setUploadProgress(prevProgress => ({
                                ...prevProgress,
                                [file.name]: percentCompleted
                            }));
                        }
                    });
    
                    if (response.data.filenames) {
                        uploadedFileNames.push(...response.data.filenames);
                        setUploadedFiles(prev => [...prev, file.name]);
                    }
                } catch (error) {
                    console.error('Error uploading chunk:', error);
                    setUploading(false);
                    return;
                }
    
                start += CHUNK_SIZE;
                chunkIndex++; // Increment chunk index
            }
        }
    
        setUploading(false);
        if (onUploadSuccess) {
            onUploadSuccess(uploadedFileNames);
        }
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

                            {/* Show progress bar while uploading */}
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
