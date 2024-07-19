import React from 'react';

const DataReview = ({ extractedData, originalLines, outputFormat }) => {
    const renderData = () => {
        if (outputFormat === 'json') {
            console.log('Extracted Data:', extractedData);
            return <pre>{JSON.stringify(extractedData, null, 2)}</pre>;
        } else if (outputFormat === 'csv') {
            console.log('Extracted Data:', extractedData);
            if (!extractedData || !extractedData.csv_data) {
                console.log('No CSV data available, Please change the output format to "CSV" above and extract data again.');
                return <div>No CSV data available</div>;
            }
            const csvData = extractedData.csv_data.trim();
            const rows = csvData.split('\n').map(row => row.split(','));
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
            let textData = '';
            Object.keys(extractedData).forEach(filename => {
                textData += `File: ${filename}\n`;
                textData += Object.entries(extractedData[filename]).map(([key, value]) => `${key}: ${value}`).join('\n');
                textData += '\n';
            });
            return <pre>{textData}</pre>;
        } else {
            console.log('Invalid output format');
            return null;
        }
    };

    const downloadData = (format) => {
        let dataStr;
        let fileName;
        if (format === 'json') {
            dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(extractedData, null, 2));
            fileName = "extracted_data.json";
        } else if (format === 'csv') {
            dataStr = "data:text/csv;charset=utf-8," + encodeURIComponent(extractedData.csv_data);
            fileName = "extracted_data.csv";
        } else if (format === 'text') {
            let textData = '';
            Object.keys(extractedData).forEach(filename => {
                textData += `File: ${filename}\n`;
                textData += Object.entries(extractedData[filename]).map(([key, value]) => `${key}: ${value}`).join('\n');
                textData += '\n';
            });
            dataStr = "data:text/plain;charset=utf-8," + encodeURIComponent(textData);
            fileName = "extracted_data.txt";
        }
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", fileName);
        document.body.appendChild(downloadAnchorNode); // required for firefox
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    return (
        <div>
            <h2>Review Extracted Data</h2>
            {renderData()}
            <button onClick={() => downloadData(outputFormat)}>Download {outputFormat.toUpperCase()}</button>
            <h3>Original Lines</h3>
            {Object.keys(originalLines).map(filename => (
                <div key={filename}>
                    <h4>{filename}</h4>
                    <pre>{originalLines[filename].join('\n')}</pre>
                </div>
            ))}
        </div>
    );
};

export default DataReview;
