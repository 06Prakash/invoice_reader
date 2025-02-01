import React, { useState, useEffect } from 'react';
import './styles/DataReview.css';

const DataReview = ({ extractedData, originalLines }) => {
    const [selectedFile, setSelectedFile] = useState('');
    const [currentFormat, setCurrentFormat] = useState('');
    const [availableFormats, setAvailableFormats] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 100;

    const fileList = Object.keys(extractedData.json_data || {});

    // Dynamically update available formats based on the selected file
    useEffect(() => {
        if (selectedFile) {
            const formats = [];
            if (extractedData.json_data[selectedFile]) formats.push('json');
            if (extractedData.csv_data[selectedFile]) formats.push('csv');
            if (extractedData.excel_paths[selectedFile]) formats.push('excel');
            if (extractedData.text_data[selectedFile]) formats.push('text');
            // Safely handle combined_excel_paths
            if (extractedData.combined_excel_paths[selectedFile]) formats.push('combined_excel');
            setAvailableFormats(formats);
            setCurrentFormat(formats[0] || ''); // Default to the first available format
        } else {
            setAvailableFormats([]);
            setCurrentFormat('');
        }
    }, [selectedFile, extractedData]);

    const handleFileSelection = (fileName) => {
        setSelectedFile(fileName);
        setCurrentPage(1); // Reset pagination when changing files
    };

    const handleFormatChange = (event) => {
        setCurrentFormat(event.target.value);
    };

    const renderData = () => {
        if (!selectedFile || !currentFormat) {
            return <p>Please select a file and format to view its content.</p>;
        }

        const formatPaths = {
            json: extractedData.json_data[selectedFile],
            csv: extractedData.csv_data[selectedFile],
            excel: extractedData.excel_paths[selectedFile],
            text: extractedData.text_data[selectedFile],
            combined_excel: extractedData.combined_excel_paths[selectedFile]
        };     

        const path = formatPaths[currentFormat];

        if (path) {
            return (
                <div>
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
                        {availableFormats.map((format) => (
                            <option key={format} value={format}>
                                {format.toUpperCase()}
                            </option>
                        ))}
                    </select>
                </div>
            )}
            <div className="data-viewer">{renderData()}</div>
            <div className="original-lines-viewer">{renderOriginalLines()}</div>
        </div>
    );
};

export default DataReview;
