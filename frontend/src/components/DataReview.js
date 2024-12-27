import React, { useState } from 'react';
import './styles/DataReview.css';

const DataReview = ({ extractedData, originalLines }) => {
    const [selectedFile, setSelectedFile] = useState('');
    const [currentFormat, setCurrentFormat] = useState('json');
    const [currentPaths, setCurrentPaths] = useState({});
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 100;

    const fileList = Object.keys(extractedData.json_data || {});

    const handleFileSelection = (fileName) => {
        setSelectedFile(fileName);
        setCurrentFormat('json'); // Reset format to JSON on file selection
        setCurrentPaths({}); // Clear any previous paths when a new file is selected
    };

    const handleFormatChange = (event) => {
        const format = event.target.value;
        setCurrentFormat(format);
    
        if (selectedFile) {
            // Dynamically fetch and store the relevant path for the selected file and format
            let path = '';
            if (format === 'json') {
                path = extractedData.json_data[selectedFile];
            } else if (format === 'csv') {
                path = extractedData.csv_data[selectedFile];
            } else if (format === 'excel') {
                path = extractedData.excel_paths[selectedFile];
            } else if (format === 'text') {
                path = extractedData.text_data[selectedFile];
            }
    
            setCurrentPaths((prevPaths) => ({
                ...prevPaths,
                [format]: path || '',
            }));
        }
    };    

    const renderData = () => {
        if (!selectedFile) {
            return <p>Please select a file to view its content.</p>;
        }

        const path = currentPaths[currentFormat];
        if (path) {
            return (
                <div>
                    {/* <p>{currentFormat.toUpperCase()} Path: {path}</p> */}
                    <button onClick={() => downloadFile(path)}>
                        Download {currentFormat.toUpperCase()}
                    </button>
                </div>
            );
        }

        return <p>Selected format is not available for the selected file.</p>;
    };

    const renderOriginalLines = () => {
        if (!selectedFile || !originalLines[selectedFile]) {
            return <p>No original lines available for the selected file.</p>;
        }

        const lines = originalLines[selectedFile].split('\n');
        const totalPages = Math.ceil(lines.length / itemsPerPage);

        const paginate = (pageNum) => {
            setCurrentPage(pageNum);
        };

        const renderPagination = () => {
            const pages = [];
            for (let i = 1; i <= totalPages; i++) {
                pages.push(
                    <button
                        key={i}
                        onClick={() => paginate(i)}
                        className={currentPage === i ? 'active' : ''}
                    >
                        {i}
                    </button>
                );
            }
            return <div className="pagination">{pages}</div>;
        };

        const currentLines = lines.slice(
            (currentPage - 1) * itemsPerPage,
            currentPage * itemsPerPage
        );

        return (
            <div className="original-lines">
                <h3>Original Lines</h3>
                <pre>{currentLines.join('\n')}</pre>
                {renderPagination()}
            </div>
        );
    };

    const downloadFile = (filePath) => {
        const fileName = filePath.split('/').pop();
        const downloadUrl = `/downloads/${fileName}`;
        fetch(downloadUrl, {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${localStorage.getItem('jwt_token')}`,
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Failed to download file.');
                }
                return response.blob();
            })
            .then((blob) => {
                const blobUrl = window.URL.createObjectURL(blob);
                const downloadAnchorNode = document.createElement('a');
                downloadAnchorNode.href = blobUrl;
                downloadAnchorNode.download = fileName;
                document.body.appendChild(downloadAnchorNode);
                downloadAnchorNode.click();
                downloadAnchorNode.remove();
                window.URL.revokeObjectURL(blobUrl);
            })
            .catch((error) => {
                console.error('Error downloading file:', error);
            });
    };

    return (
        <div className="data-review-container">
            <h2>Review Extracted Data</h2>
            <div className="file-selection">
                <label>Select File:</label>
                <select value={selectedFile} onChange={(e) => handleFileSelection(e.target.value)}>
                    <option value="">-- Select a file --</option>
                    {fileList.map((file) => (
                        <option key={file} value={file}>
                            {file}
                        </option>
                    ))}
                </select>
            </div>
            {selectedFile && (
                <div className="format-selection">
                    <label>Select Format:</label>
                    <select value={currentFormat} onChange={handleFormatChange}>
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                        <option value="excel">Excel</option>
                        <option value="text">Text</option>
                    </select>
                </div>
            )}
            <div className="data-viewer">{renderData()}</div>
            <div className="original-lines-viewer">{renderOriginalLines()}</div>
        </div>
    );
};

export default DataReview;
