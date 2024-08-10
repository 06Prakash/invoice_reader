import React, { useState } from 'react';
import axios from 'axios';
import { Button, CircularProgress } from '@mui/material';
import './styles/UploadComponent.css';

const UploadComponent = ({ onUploadSuccess }) => {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [uploading, setUploading] = useState(false);

    const handleFileChange = (e) => {
        setSelectedFiles(e.target.files);
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            alert('Please select files first');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < selectedFiles.length; i++) {
            formData.append('files', selectedFiles[i]);
        }

        setUploading(true);

        try {
            const response = await axios.post('/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            onUploadSuccess(response.data.filenames);
        } catch (error) {
            console.error('Error uploading files:', error);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="upload-container">
            <label className="custom-file-upload">
                <input type="file" multiple onChange={handleFileChange} />
                Choose Files
            </label>
            {selectedFiles.length > 0 && (
                <span className="file-count">{selectedFiles.length} file(s) selected</span>
            )}
            <Button variant="contained" className="upload-button" onClick={handleUpload} disabled={uploading}>
                {uploading ? <CircularProgress size={24} /> : 'Upload'}
            </Button>
        </div>
    );
};

export default UploadComponent;
