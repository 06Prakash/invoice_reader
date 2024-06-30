import React from 'react';

const DataReview = ({ extractedData, outputFormat }) => {
    const renderExtractedData = () => {
        if (outputFormat === 'json') {
            return <pre>{JSON.stringify(extractedData, null, 2)}</pre>;
        } else if (outputFormat === 'csv') {
            return <pre>{extractedData}</pre>;
        } else if (outputFormat === 'text') {
            return <pre>{extractedData}</pre>;
        } else {
            return <pre>{JSON.stringify(extractedData, null, 2)}</pre>;
        }
    };

    return (
        <div>
            <h2>Review Extracted Data</h2>
            {renderExtractedData()}
        </div>
    );
};

export default DataReview;
