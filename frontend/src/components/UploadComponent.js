import React, { useState } from 'react';
import axios from 'axios';

const UploadComponent = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setMessage('');
    };

    const handleUpload = () => {
        if (!file) {
            setMessage('Please select a file to upload.');
            return;
        }
        setLoading(true);
        setMessage('');
        const formData = new FormData();
        formData.append('file', file);

        axios.post('http://localhost:5001/upload', formData)
            .then(response => {
                console.log('File uploaded successfully:', response.data);
                onUploadSuccess(response.data.filename);
                setMessage('File uploaded successfully.');
            })
            .catch(error => {
                console.error('Error uploading file:', error);
                setMessage('Failed to upload the file.');
            })
            .finally(() => {
                setLoading(false);
            });
    };

    return (
        <div>
            <h3>Upload PDF</h3>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleUpload} disabled={loading}>
                {loading ? 'Uploading...' : 'Upload'}
            </button>
            {message && <p>{message}</p>}
        </div>
    );
};

export default UploadComponent;
