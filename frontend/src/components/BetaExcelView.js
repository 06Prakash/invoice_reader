import 'react-data-grid/lib/styles.css';
import React, { useState, useEffect, useCallback } from 'react';
import { FaUndo, FaRedo, FaDownload, FaSyncAlt } from "react-icons/fa";
import * as XLSX from 'xlsx';
import DataGrid from 'react-data-grid';
import './styles/BetaExcelView.css';

const BetaExcelView = () => {
    // State variables
    const [rows, setRows] = useState([]);
    const [columns, setColumns] = useState([]);
    const [selectedFile, setSelectedFile] = useState('');
    const [selectedSheet, setSelectedSheet] = useState('');
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [selectedColumn, setSelectedColumn] = useState('');
    const [reductionFactor, setReductionFactor] = useState(1);

    // Mock Excel data - completely frontend
    const mockExcelFiles = {
        'document1.xlsx': {
            sheets: ['Sheet1', 'Sheet2'],
            data: {
                Sheet1: [
                    ['Name', 'Age', 'Email'],
                    ['John Doe', 32, 'john@example.com'],
                    ['Jane Smith', 28, 'jane@example.com']
                ],
                Sheet2: [
                    ['Product', 'Price', 'Stock'],
                    ['Laptop', 999, 15],
                    ['Phone', 699, 30]
                ]
            }
        },
        'document2.xlsx': {
            sheets: ['Data', 'Summary'],
            data: {
                Data: [
                    ['ID', 'Value', 'Date'],
                    [1, 150, '2023-01-01'],
                    [2, 200, '2023-01-02']
                ],
                Summary: [
                    ['Total', 'Average'],
                    [350, 175]
                ]
            }
        }
    };

    // Load sheet data from mock files
    const loadSheetData = useCallback((filename, sheetname) => {
        const fileData = mockExcelFiles[filename];
        if (!fileData || !fileData.data[sheetname]) return;

        const sheetData = fileData.data[sheetname];
        
        // Create columns
        const newColumns = sheetData[0].map((header, index) => ({
            key: `col-${index}`,
            name: header.toString(),
            editable: true,
            width: 150,
            resizable: true,
            editor: ({ row, column, onRowChange }) => (
                <input
                    type="text"
                    value={row[column.key] || ""}
                    onChange={(e) => onRowChange({ ...row, [column.key]: e.target.value })}
                    autoFocus
                />
            )
        }));

        // Create rows
        const newRows = sheetData.slice(1).map((row, rowIndex) => {
            const rowObj = { id: rowIndex };
            newColumns.forEach((col, colIndex) => {
                rowObj[col.key] = row[colIndex] !== undefined ? row[colIndex] : "";
            });
            return rowObj;
        });

        setColumns(newColumns);
        setRows(newRows);
        setHistory([{ rows: newRows, columns: newColumns }]);
        setHistoryIndex(0);
    }, []);

    // Handle file selection
    const handleFileChange = (e) => {
        const filename = e.target.value;
        setSelectedFile(filename);
        if (filename && mockExcelFiles[filename]) {
            setSelectedSheet(mockExcelFiles[filename].sheets[0]);
            loadSheetData(filename, mockExcelFiles[filename].sheets[0]);
        }
    };

    // Handle sheet selection
    const handleSheetChange = (e) => {
        const sheetname = e.target.value;
        setSelectedSheet(sheetname);
        loadSheetData(selectedFile, sheetname);
    };

    // Handle grid changes
    const handleGridChange = (newRows) => {
        setRows(newRows);
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push({ rows: newRows, columns });
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
    };

    // Undo functionality
    const undo = () => {
        if (historyIndex > 0) {
            const prevState = history[historyIndex - 1];
            setRows(prevState.rows);
            setColumns(prevState.columns);
            setHistoryIndex(historyIndex - 1);
        }
    };

    // Redo functionality
    const redo = () => {
        if (historyIndex < history.length - 1) {
            const nextState = history[historyIndex + 1];
            setRows(nextState.rows);
            setColumns(nextState.columns);
            setHistoryIndex(historyIndex + 1);
        }
    };

    // Column reduction
    const applyColumnReduction = () => {
        if (!selectedColumn) return;
        
        const newRows = rows.map(row => {
            const value = row[selectedColumn];
            const numValue = typeof value === 'string' ? parseFloat(value) : value;
            const reducedValue = !isNaN(numValue) ? (numValue / reductionFactor).toFixed(2) : value;
            return { ...row, [selectedColumn]: reducedValue };
        });

        const newColumns = columns.map(col => 
            col.key === selectedColumn 
                ? { ...col, name: `${col.name} (÷${reductionFactor})` } 
                : col
        );

        setRows(newRows);
        setColumns(newColumns);
        
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push({ rows: newRows, columns: newColumns });
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
    };

    // Export to Excel
    const exportToExcel = () => {
        const worksheet = XLSX.utils.json_to_sheet(
            rows.map(row => {
                const obj = {};
                columns.forEach(col => {
                    obj[col.name] = row[col.key];
                });
                return obj;
            })
        );
        
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, selectedSheet);
        XLSX.writeFile(workbook, `${selectedFile}-edited.xlsx`);
    };

    // Reset to original data
    const resetData = () => {
        if (selectedFile && selectedSheet) {
            loadSheetData(selectedFile, selectedSheet);
        }
    };

    return (
        <div className="beta-excel-container">
            <h2>Excel Data Editor (Beta)</h2>
            
            <div className="controls">
                <div className="file-control">
                    <label>File:</label>
                    <select value={selectedFile} onChange={handleFileChange}>
                        <option value="">Select a file</option>
                        {Object.keys(mockExcelFiles).map(file => (
                            <option key={file} value={file}>{file}</option>
                        ))}
                    </select>
                </div>
                
                {selectedFile && (
                    <div className="sheet-control">
                        <label>Sheet:</label>
                        <select value={selectedSheet} onChange={handleSheetChange}>
                            {mockExcelFiles[selectedFile].sheets.map(sheet => (
                                <option key={sheet} value={sheet}>{sheet}</option>
                            ))}
                        </select>
                    </div>
                )}
                
                <div className="column-control">
                    <label>Column:</label>
                    <select 
                        value={selectedColumn} 
                        onChange={(e) => setSelectedColumn(e.target.value)}
                        disabled={columns.length === 0}
                    >
                        <option value="">Select column</option>
                        {columns.map(col => (
                            <option key={col.key} value={col.key}>{col.name}</option>
                        ))}
                    </select>
                </div>
                
                <div className="factor-control">
                    <label>Divide by:</label>
                    <input
                        type="number"
                        min="1"
                        step="0.1"
                        value={reductionFactor}
                        onChange={(e) => setReductionFactor(Number(e.target.value))}
                    />
                    <button 
                        onClick={applyColumnReduction}
                        disabled={!selectedColumn}
                    >
                        Apply
                    </button>
                </div>
            </div>
            
            <div className="action-buttons">
                <button onClick={undo} disabled={historyIndex <= 0}>
                    <FaUndo /> Undo
                </button>
                <button onClick={redo} disabled={historyIndex >= history.length - 1}>
                    <FaRedo /> Redo
                </button>
                <button onClick={resetData} disabled={!selectedFile}>
                    <FaSyncAlt /> Reset
                </button>
                <button onClick={exportToExcel} disabled={rows.length === 0}>
                    <FaDownload /> Export
                </button>
            </div>
            
            <div className="grid-container">
                {rows.length > 0 ? (
                    <DataGrid
                        columns={columns}
                        rows={rows}
                        onRowsChange={handleGridChange}
                        rowHeight={35}
                        headerRowHeight={40}
                        style={{ height: '500px' }}
                    />
                ) : (
                    <div className="no-data">
                        {selectedFile ? 'Select a sheet to view data' : 'Select a file to begin'}
                    </div>
                )}
            </div>
        </div>
    );
};

export default BetaExcelView;