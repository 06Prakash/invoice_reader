import React from 'react';

const DataReview = ({ extractedData, outputFormat, originalLines }) => {
    const renderData = () => {
        if (outputFormat === 'json') {
            return <pre>{JSON.stringify(extractedData, null, 2)}</pre>;
        } else if (outputFormat === 'csv') {
            // Render CSV data
            const csvRows = [Object.keys(extractedData), Object.values(extractedData)];
            return (
                <table>
                    <thead>
                        <tr>
                            {csvRows[0].map((header, index) => (
                                <th key={index}>{header}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            {csvRows[1].map((value, index) => (
                                <td key={index}>{value}</td>
                            ))}
                        </tr>
                    </tbody>
                </table>
            );
        } else if (outputFormat === 'txt') {
            return <pre>{extractedData}</pre>;
        } else {
            return null;
        }
    };

    return (
        <div>
            <h2>Review Extracted Data</h2>
            {renderData()}
            <h3>Original Lines</h3>
            {originalLines && originalLines.map((line, index) => (
                <pre key={index}>{line}</pre>
            ))}
        </div>
    );
};

export default DataReview;
