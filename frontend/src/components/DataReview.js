import React, { useState } from 'react';
import './DataReview.css';

const DataReview = ({ extractedData, originalLines, outputFormat }) => {
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 5;

    const renderData = () => {
        if (outputFormat === 'json') {
            console.log('Extracted Data:', extractedData);
            return <pre>{JSON.stringify(extractedData.json_data, null, 2)}</pre>;
        } else if (outputFormat === 'csv') {
            console.log('Extracted Data:', extractedData);
            if (!extractedData || !extractedData.csv_data) {
                console.log('No CSV data available, Please change the output format to "CSV" above and extract data again.');
                return <div>No CSV data available</div>;
            }
            const csvData = extractedData.csv_data.trim();
            const rows = csvData.split('\n').map(row => row.split(','));
            return (
                <table>
                    <thead>
                        <tr>
                            {rows[0].map((header, index) => (
                                <th key={index}>{header}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.slice(1).map((row, index) => (
                            <tr key={index}>
                                {row.map((value, idx) => (
                                    <td key={idx}>{value}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            );
        } else if (outputFormat === 'text') {
            console.log('Extracted Data:', extractedData);
            let textData = '';
            textData = extractedData.text_data;
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
            dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(extractedData.json_data, null, 2));
            fileName = "extracted_data.json";
        } else if (format === 'csv') {
            dataStr = "data:text/csv;charset=utf-8," + encodeURIComponent(extractedData.csv_data);
            fileName = "extracted_data.csv";
        } else if (format === 'text') {
            dataStr = "data:text/plain;charset=utf-8," + encodeURIComponent(extractedData.text_data);
            fileName = "extracted_data.txt";
        }
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", fileName);
        document.body.appendChild(downloadAnchorNode); // required for firefox
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    const totalPages = Math.ceil(Object.keys(originalLines).length / itemsPerPage);

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

    return (
        <div className="data-review">
            <h2>Review Extracted Data</h2>
            {renderData()}
            <button className="download-button" onClick={() => downloadData(outputFormat)}>Download {outputFormat.toUpperCase()}</button>
            <h3>Original Lines</h3>
            {Object.keys(originalLines)
                .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                .map(filename => (
                    <div key={filename}>
                        <h4>{filename}</h4>
                        <pre>{originalLines[filename].join('\n')}</pre>
                    </div>
                ))}
            {renderPagination()}
        </div>
    );
};

export default DataReview;
