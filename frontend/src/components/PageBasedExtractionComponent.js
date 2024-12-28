import React, { useState } from 'react';
import './styles/PageBasedExtractionComponent.css';

const PageBasedExtractionComponent = ({ onPageExtractionConfigSubmit, uploadedFiles = [] }) => {
    const [pageConfig, setPageConfig] = useState({});
    const [filename, setFilename] = useState('');
    const [section, setSection] = useState('');
    const [pageRange, setPageRange] = useState('');
    const [notification, setNotification] = useState('');
    const [isExpanded, setIsExpanded] = useState(false);

    const handleInputChange = (file, section, value) => {
        setPageConfig((prevConfig) => ({
            ...prevConfig,
            [file]: {
                ...prevConfig[file],
                [section]: value,
            },
        }));
    };

    const handleAddSectionConfig = () => {
        if (!filename || !section || !pageRange) {
            alert('Please provide a filename, section, and page range.');
            return;
        }

        const sanitizedFilename = filename.replace(/\s+/g, '_'); // Replace spaces with underscores
        setPageConfig((prevConfig) => ({
            ...prevConfig,
            [sanitizedFilename]: {
                ...prevConfig[sanitizedFilename],
                [section]: pageRange,
            },
        }));
        setSection('');
        setPageRange('');
    };

    const handleRemoveSection = (file, sectionToRemove) => {
        setPageConfig((prevConfig) => {
            const updatedConfig = { ...prevConfig };
            delete updatedConfig[file][sectionToRemove];
            if (Object.keys(updatedConfig[file]).length === 0) {
                delete updatedConfig[file];
            }
            return updatedConfig;
        });
    };

    const handleResetConfig = () => {
        setPageConfig({});
        setFilename('');
        setSection('');
        setPageRange('');
    };

    const handleSubmit = () => {
        onPageExtractionConfigSubmit(pageConfig);
        setNotification('Page configuration submitted successfully!');
        setTimeout(() => setNotification(''), 3000); // Clear notification after 3 seconds
    };

    const toggleExpandCollapse = () => {
        setIsExpanded(!isExpanded);
    };

    return (
        <div className="page-extraction-container">
            <h3 onClick={toggleExpandCollapse} className="expand-collapse-header">
                {isExpanded ? '▼ Page-Based Extraction' : '▶ Page-Based Extraction'}
            </h3>
            {isExpanded && (
                <div className="page-extraction-content">
                    <p>
                        Specify the pages to extract for each file and section. Use the reset button to clear all configurations or remove individual sections as needed.
                    </p>
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
                                        <button onClick={() => handleRemoveSection(file, section)}>Remove Section</button>
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>

                    <div className="add-section">
                        <select
                            value={filename}
                            onChange={(e) => setFilename(e.target.value)}
                            className="file-dropdown"
                        >
                            <option value="" disabled>
                                Select a file
                            </option>
                            {Array.isArray(uploadedFiles) &&
                                uploadedFiles.map((file) => (
                                    <option key={file} value={file}>
                                        {file}
                                    </option>
                                ))}
                        </select>
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

                    <div className="json-actions">
                        <button onClick={handleResetConfig}>Reset All Configurations</button>
                        <button
                            onClick={handleSubmit}
                            className="submit-button"
                            onMouseDown={(e) => e.target.classList.add('clicked')}
                            onMouseUp={(e) => e.target.classList.remove('clicked')}
                        >
                            Submit Page Configuration
                        </button>
                    </div>

                    {notification && <p className="notification">{notification}</p>}
                </div>
            )}
        </div>
    );
};

export default PageBasedExtractionComponent;
