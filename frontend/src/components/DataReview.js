import React, { useState, useEffect } from 'react';
import BetaExcelView from './BetaExcelView';
import './styles/DataReview.css';

const DataReview = ({ extractedData, originalLines }) => {
    const [isBetaView, setIsBetaView] = useState(false);
    const [selectedFile, setSelectedFile] = useState('');

    return (
        <div className="data-review">
            <div className="view-toggle">
                <label>
                    <input 
                        type="checkbox" 
                        checked={isBetaView}
                        onChange={() => setIsBetaView(!isBetaView)}
                    />
                    Enable Beta Excel View
                </label>
            </div>
            
            {isBetaView ? (
                <BetaExcelView extractedData={extractedData} />
            ) : (
                <div className="standard-view">
                    <select 
                        value={selectedFile} 
                        onChange={(e) => setSelectedFile(e.target.value)}
                    >
                        <option value="">Select a file</option>
                        {extractedData && Object.keys(extractedData.json_data || {}).map(file => (
                            <option key={file} value={file}>{file}</option>
                        ))}
                    </select>
                    
                    {selectedFile && (
                        <div className="file-preview">
                            <h3>Original Text:</h3>
                            <pre>{originalLines[selectedFile]}</pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default DataReview;
