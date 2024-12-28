import React, { useState } from 'react';
import './styles/PageBasedExtractionComponent.css';

const PageBasedExtractionComponent = ({ onPageExtractionConfigSubmit }) => {
    const [pageConfig, setPageConfig] = useState({});
    const [uploadedJson, setUploadedJson] = useState(null);
    const [filename, setFilename] = useState('');
    const [section, setSection] = useState('');
    const [pageRange, setPageRange] = useState('');

    const handleInputChange = (file, section, value) => {
        setPageConfig((prevConfig) => ({
            ...prevConfig,
            [file]: {
                ...prevConfig[file],
                [section]: value,
            },
        }));
    };

    const handleJsonUpload = (event) => {
        const file = event.target.files[0];
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const jsonContent = JSON.parse(e.target.result);
                setPageConfig(jsonContent);
                setUploadedJson(file.name);
            } catch (error) {
                alert('Invalid JSON file. Please upload a valid JSON.');
            }
        };
        reader.readAsText(file);
    };

    const handleAddSectionConfig = () => {
        if (!filename || !section || !pageRange) {
            alert('Please provide a filename, section, and page range.');
            return;
        }
        setPageConfig((prevConfig) => ({
            ...prevConfig,
            [filename]: {
                ...prevConfig[filename],
                [section]: pageRange,
            },
        }));
        setSection('');
        setPageRange('');
    };

    const handleSubmit = () => {
        console.log('Submitting Page Config:', pageConfig);
        onPageExtractionConfigSubmit(pageConfig);
    };

    const handleDownloadJson = () => {
        const jsonContent = JSON.stringify(pageConfig, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'page_config.json';
        link.click();
    };

    return (
        <div className="page-extraction-container">
            <h3>Page-Based Extraction</h3>
            <p>Specify the pages to extract for each file and section:</p>
            <div className="file-inputs">
                {Object.keys(pageConfig).length === 0 && <p>No files added yet.</p>}
                {Object.entries(pageConfig).map(([file, sections]) => (
                    <div key={file} className="file-config">
                        <h4>{file}</h4>
                        {Object.entries(sections).map(([section, range]) => (
                            <div key={section} className="section-config">
                                <label>{section}:</label>
                                <input
                                    type="text"
                                    placeholder="e.g., 1,3-4"
                                    value={range || ''}
                                    onChange={(e) => handleInputChange(file, section, e.target.value)}
                                />
                            </div>
                        ))}
                    </div>
                ))}
            </div>

            <div className="add-section">
                <input
                    type="text"
                    placeholder="Enter filename (e.g., file1.pdf)"
                    value={filename}
                    onChange={(e) => setFilename(e.target.value)}
                />
                <input
                    type="text"
                    placeholder="Enter section name (e.g., Table 1)"
                    value={section}
                    onChange={(e) => setSection(e.target.value)}
                />
                <input
                    type="text"
                    placeholder="Enter page range (e.g., 1,3-4)"
                    value={pageRange}
                    onChange={(e) => setPageRange(e.target.value)}
                />
                <button onClick={handleAddSectionConfig}>Add Section</button>
            </div>

            <div className="json-upload">
                <p>Or upload a JSON configuration file:</p>
                <input type="file" accept=".json" onChange={handleJsonUpload} />
                {uploadedJson && <p>Uploaded JSON: {uploadedJson}</p>}
            </div>

            <div className="json-actions">
                <button onClick={handleDownloadJson}>Download JSON</button>
                <button onClick={handleSubmit}>Submit Page Configuration</button>
            </div>
        </div>
    );
};

export default PageBasedExtractionComponent;
