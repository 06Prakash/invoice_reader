import React, { useState } from 'react';
import './styles/PageBasedExtractionComponent.css';

const PageBasedExtractionComponent = ({ onPageExtractionConfigSubmit, uploadedFiles = [] }) => {
    const [pageConfig, setPageConfig] = useState({});
    const [filename, setFilename] = useState('');
    const [section, setSection] = useState('');
    const [pageRange, setPageRange] = useState('');
    const [columnsToRemove, setColumnsToRemove] = useState('');
    const [rowsToRemove, setRowsToRemove] = useState('');
    const [gridLinesRemoval, setGridLinesRemoval] = useState(false);
    const [errors, setErrors] = useState({ section: '', pageRange: '' });
    const [notification, setNotification] = useState('');
    const [isExpanded, setIsExpanded] = useState(false);

    const validateSectionName = (name) => {
        const sectionNameRegex = /^[a-zA-Z0-9_-]{1,50}$/; // Only letters, digits, '-', '_', max 50 characters
        return sectionNameRegex.test(name);
    };

    const validatePageRange = (range) => {
        const pageRangeRegex = /^(\d+(-\d+)?)(,\d+(-\d+)?)*$/; // Valid patterns: 1, 1-3, 1-3,4
        return pageRangeRegex.test(range);
    };

    const handleSectionChange = (value) => {
        setSection(value);
        if (!validateSectionName(value)) {
            setErrors((prevErrors) => ({
                ...prevErrors,
                section: 'Invalid section name. Only letters, digits, "-", and "_" are allowed (max 50 characters).',
            }));
        } else {
            setErrors((prevErrors) => ({ ...prevErrors, section: '' }));
        }
    };

    const handlePageRangeChange = (value) => {
        setPageRange(value);
        if (!validatePageRange(value)) {
            setErrors((prevErrors) => ({
                ...prevErrors,
                pageRange: 'Invalid page range. Use formats like "1", "1-3", or "1-3,4".',
            }));
        } else {
            setErrors((prevErrors) => ({ ...prevErrors, pageRange: '' }));
        }
    };

    const handleInputChange = (file, section, category, key, value) => {
        setPageConfig((prevConfig) => ({
            ...prevConfig,
            [file]: {
                ...prevConfig[file],
                [section]: {
                    ...prevConfig[file][section],
                    [category]: {
                        ...prevConfig[file][section]?.[category],
                        [key]: value,
                    },
                },
            },
        }));
    };

    const handleAddSectionConfig = () => {
        if (!filename || !section || !pageRange) {
            alert('Please provide a filename, section, and page range.');
            return;
        }

        if (!validateSectionName(section)) {
            alert('Section name is invalid. Only letters, digits, "-", "_" are allowed, with a max length of 50.');
            return;
        }

        if (!validatePageRange(pageRange)) {
            alert('Page range is invalid. Use formats like "1", "1-3", "1-3,4".');
            return;
        }

        const sanitizedFilename = filename.replace(/\s+/g, '_'); // Replace spaces with underscores
        setPageConfig((prevConfig) => ({
            ...prevConfig,
            [sanitizedFilename]: {
                ...prevConfig[sanitizedFilename],
                [section]: {
                    pageRange,
                    excel: {
                        columnsToRemove: columnsToRemove.split(',').map((col) => col.trim()), // Convert to array
                        rowsToRemove: rowsToRemove.split(',').map((row) => row.trim()), // Convert to array
                        gridLinesRemoval,
                    },
                },
            },
        }));
        setSection('');
        setPageRange('');
        setColumnsToRemove('');
        setRowsToRemove('');
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
        setColumnsToRemove('');
        setRowsToRemove('');
        setGridLinesRemoval(false);
        setErrors({ section: '', pageRange: '' });

        if (onPageExtractionConfigSubmit) {
            onPageExtractionConfigSubmit({}); // Notify backend to clear configurations
        }

        setNotification('Configuration reset successfully!');
        setTimeout(() => setNotification(''), 3000);
    };

    const handleSubmit = () => {
        if (errors.section || errors.pageRange) {
            alert('Please fix validation errors before submitting.');
            return;
        }
        onPageExtractionConfigSubmit(pageConfig);
        setNotification('Page configuration submitted successfully!');
        setTimeout(() => setNotification(''), 3000);
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
                                {Object.entries(sections).map(([section, config]) => (
                                    <div key={section} className="section-config">
                                        <label>{section}:</label>
                                        <input
                                            type="text"
                                            placeholder="e.g., 1,3-4"
                                            value={config.pageRange || ''}
                                            onChange={(e) =>
                                                handleInputChange(file, section, 'general', 'pageRange', e.target.value)
                                            }
                                        />
                                        <input
                                            type="text"
                                            placeholder="Columns to remove (comma-separated)"
                                            value={config.excel?.columnsToRemove?.join(', ') || ''}
                                            onChange={(e) =>
                                                handleInputChange(
                                                    file,
                                                    section,
                                                    'excel',
                                                    'columnsToRemove',
                                                    e.target.value.split(',').map((col) => col.trim())
                                                )
                                            }
                                        />
                                        <input
                                            type="text"
                                            placeholder="Rows to remove (comma-separated)"
                                            value={config.excel?.rowsToRemove?.join(', ') || ''}
                                            onChange={(e) =>
                                                handleInputChange(
                                                    file,
                                                    section,
                                                    'excel',
                                                    'rowsToRemove',
                                                    e.target.value.split(',').map((row) => row.trim())
                                                )
                                            }
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
                        <div className="input-wrapper">
                            {errors.section && <p className="error-message">{errors.section}</p>}
                            <input
                                type="text"
                                placeholder="Enter section name (e.g., Table_1)"
                                value={section}
                                onChange={(e) => handleSectionChange(e.target.value)}
                                className={errors.section ? 'error' : ''}
                            />
                        </div>
                        <div className="input-wrapper">
                            {errors.pageRange && <p className="error-message">{errors.pageRange}</p>}
                            <input
                                type="text"
                                placeholder="Enter page range (e.g., 1,3-4)"
                                value={pageRange}
                                onChange={(e) => handlePageRangeChange(e.target.value)}
                                className={errors.pageRange ? 'error' : ''}
                            />
                        </div>
                        <input
                            type="text"
                            placeholder="Columns to remove (comma-separated)"
                            value={columnsToRemove}
                            onChange={(e) => setColumnsToRemove(e.target.value)}
                        />
                        <input
                            type="text"
                            placeholder="Rows to remove (comma-separated)"
                            value={rowsToRemove}
                            onChange={(e) => setRowsToRemove(e.target.value)}
                        />
                        <label>
                            <input
                                type="checkbox"
                                checked={gridLinesRemoval}
                                onChange={(e) => setGridLinesRemoval(e.target.checked)}
                            />
                            Remove Gridlines
                        </label>
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
