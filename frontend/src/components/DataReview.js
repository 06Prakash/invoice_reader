import React from 'react';

const DataReview = ({ extractedData, originalLines, outputFormat }) => {
    const renderData = () => {
        if (outputFormat === 'json') {
            console.log('Extracted Data:', extractedData);
            return <pre>{JSON.stringify(extractedData, null, 2)}</pre>;
        } else if (outputFormat === 'csv') {
            console.log('Extracted Data:', extractedData);
            if (!extractedData) {
                console.log('No CSV data available, Please change the output format to "CSV" above and extract data again.');
                return <div>No CSV data available</div>;
            }
            const rows = [Object.keys(extractedData), Object.values(extractedData)];
            console.log('CSV Data:', rows);
            return (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            {rows[0].map((header, index) => (
                                <th key={index} style={{ border: '1px solid black', padding: '8px', backgroundColor: '#f2f2f2' }}>{header}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.slice(1).map((row, index) => (
                            <tr key={index}>
                                {row.map((value, idx) => (
                                    <td key={idx} style={{ border: '1px solid black', padding: '8px' }}>{value}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            );
        } else if (outputFormat === 'text') {
            console.log('Extracted Data:', extractedData);
            const textData = Object.entries(extractedData).map(([key, value]) => `${key}: ${value}`).join('\n');
            return <pre>{textData}</pre>;
        } else {
            console.log('Invalid output format');
            return null;
        }
    };

    return (
        <div>
            <h2>Review Extracted Data</h2>
            {renderData()}
            <h3>Original Lines</h3>
            <pre>{originalLines.join('\n')}</pre>
        </div>
    );
};

export default DataReview;
