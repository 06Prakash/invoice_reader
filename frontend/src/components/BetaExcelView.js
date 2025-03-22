import 'react-data-grid/lib/styles.css';
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaUndo, FaRedo, FaDownload, FaSyncAlt } from "react-icons/fa";
import * as XLSX from 'xlsx';
import DataGrid from 'react-data-grid';
import './styles/BetaExcelView.css';

const BetaExcelView = ({ extractedData }) => {
    const [excelFiles, setExcelFiles] = useState([]);
    const [selectedFile, setSelectedFile] = useState("");
    const [selectedSheet, setSelectedSheet] = useState("");
    const [sheetNames, setSheetNames] = useState({});
    const [gridRows, setGridRows] = useState([]);
    const [gridColumns, setGridColumns] = useState([]);
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [originalData, setOriginalData] = useState({});
    const [columnReduction, setColumnReduction] = useState({});
    const [selectedColumn, setSelectedColumn] = useState("");
    const [reductionFactor, setReductionFactor] = useState(1);

    const downloadedFilesRef = useRef(new Set());

    const handleCellEdit = useCallback((rowId, columnKey, newValue) => {
        setGridRows((prevRows) => {
            const updatedRows = prevRows.map(row =>
                row.id === rowId ? { ...row, [columnKey]: newValue } : row
            );
    
            setHistory(prevHistory => {
                const newHistory = prevHistory.slice(0, historyIndex + 1);
                newHistory.push({ rows: updatedRows, columns: gridColumns });
                return newHistory;
            });
    
            setHistoryIndex(prevIndex => prevIndex + 1);
            return updatedRows;
        });
    }, [historyIndex, gridColumns]);
       
    
    const loadSheetData = useCallback((file, sheet) => {
        try {
            console.log(`Loading sheet data for file: ${file}, sheet: ${sheet}`);
            
            const excelFile = excelFiles.find(f => f.name === file);
            if (!excelFile) {
                console.error(`Excel file ${file} not found.`);
                return;
            }
            console.log(`Found excel file:`, excelFile);
    
            if (!excelFile.workbook.Sheets[sheet]) {
                console.error(`Sheet ${sheet} not found in file ${file}`);
                return;
            }
            console.log(`Found sheet: ${sheet}`);
    
            const worksheet = excelFile.workbook.Sheets[sheet];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: false });
            console.log(`Converted worksheet to JSON:`, jsonData);
    
            // Column Definitions with Editable Cells
            const columns = jsonData[0]?.map((col, index) => ({
                key: `col-${index}`,
                name: col?.toString().trim() || `Column ${index + 1}`,
                editable: true,
                width: 200,
                resizable: true,
                editor: ({ row, column, onRowChange }) => (
                    <input
                        type="text"
                        value={row[column.key] || ""}
                        onChange={(e) => onRowChange({ ...row, [column.key]: e.target.value })}
                        autoFocus
                    />
                ),
                headerRenderer: ({ column }) => (
                    <input
                        type="text"
                        value={column.name}
                        onChange={(e) => {
                            const newColumns = [...columns];
                            newColumns[index].name = e.target.value;
                            setGridColumns(newColumns);
                        }}
                    />
                ),
            })) || [];
            
            console.log(`Generated columns:`, columns);
    
            const rows = jsonData.slice(1).map((row, rowIndex) => {
                const rowData = {};
                columns.forEach((col, colIndex) => {
                    rowData[col.key] = row[colIndex] !== undefined ? row[colIndex] : ""; // Ensure every column is included
                });
                return { id: rowIndex, ...rowData };
            });
            console.log(`Generated rows:`, rows);
    
            setGridColumns(columns);
            setGridRows(rows);
            setOriginalData({ file, sheet, rows, columns });
    
            setHistory([{ rows, columns }]);
            setHistoryIndex(0);
        } catch (error) {
            console.error(`Error loading sheet data:`, error);
        }
    }, [excelFiles, handleCellEdit ])
    

    /** ✅ Download and Load Excel Files */
    const downloadAndLoadExcels = useCallback(async (excelPaths, filesToDownload) => {
        console.log("Excel Paths:", excelPaths);
        console.log("Files to Download:", filesToDownload);
        const newExcelFiles = [...excelFiles];
        const newSheetNames = { ...sheetNames };
    
        for (const filePath of filesToDownload) {
            try {
                if (!filePath) continue;
    
                const cleanFileName = filePath.split('/').pop();
                if (!cleanFileName.endsWith('.xlsx') && !cleanFileName.endsWith('.xls')) {
                    console.warn(`Skipping non-Excel file: ${cleanFileName}`);
                    continue;
                }
                const fileUrl = `/downloads/${cleanFileName}`;
                console.log(`Downloading file from: ${fileUrl}`);
    
                const response = await fetch(fileUrl, {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem('jwt_token')}`,
                    },
                });
    
                if (!response.ok) throw new Error(`Failed to download: ${cleanFileName}`);
    
                const blob = await response.blob();
                const reader = new FileReader();
    
                reader.onload = (e) => {
                    try {
                        const data = new Uint8Array(e.target.result);
                        const workbook = XLSX.read(data, { type: 'array' });
    
                        newExcelFiles.push({ name: filePath, workbook });
                        newSheetNames[filePath] = workbook.SheetNames || [];
    
                        if (!selectedFile) {
                            setSelectedFile(filePath);
                            setSelectedSheet(workbook.SheetNames[0]);
                            loadSheetData(filePath, workbook.SheetNames[0]);
                        }
                    } catch (error) {
                        console.error(`Error processing file ${filePath}:`, error);
                    }
                };
                reader.readAsArrayBuffer(blob);
            } catch (error) {
                console.error(`Error fetching file ${filePath}:`, error);
            }
        }
    
        setExcelFiles(newExcelFiles);
        setSheetNames(newSheetNames);
    }, [excelFiles, sheetNames, selectedFile, loadSheetData]); // ✅ Now includes `loadSheetData`
    

     /** ✅ Process Extracted Data */
     useEffect(() => {
        if (extractedData) {
            console.log("Extracted Data as obtained by Beta Excel View:", extractedData);

            const allExcelPaths = [
                ...new Set([
                    ...Object.values(extractedData.excel_paths || {}),
                    ...Object.values(extractedData.combined_excel_paths || {})
                ])
            ];

            console.log("Processed Excel Paths:", allExcelPaths);
            console.log("Downloaded Files Ref:", Array.from(downloadedFilesRef.current));
            const newFilesToDownload = allExcelPaths
                .map((path) => path.split('/').pop())
                .filter((fileName) => !downloadedFilesRef.current.has(fileName));
            console.log("New Files to Download:", newFilesToDownload);

            if (newFilesToDownload.length > 0) {
                downloadAndLoadExcels(extractedData.excel_paths, newFilesToDownload);
                newFilesToDownload.forEach((fileName) => downloadedFilesRef.current.add(fileName));
            }
        }
    }, [extractedData, downloadAndLoadExcels]);
    
    /** ✅ Handles File Selection */
    const handleFileSelection = (fileName) => {
        setSelectedFile(fileName);
        if (sheetNames[fileName]?.length > 0) {
            setSelectedSheet(sheetNames[fileName][0]);
            loadSheetData(fileName, sheetNames[fileName][0]);
        }
    };


    /** ✅ Handles Sheet Selection */
    const handleSheetSelection = (sheetName) => {
        setSelectedSheet(sheetName);
        loadSheetData(selectedFile, sheetName);
    };

    /** ✅ Handles Grid Changes */
    const handleGridChange = (updatedRows) => {
        if (!updatedRows || updatedRows.length === 0) return; // ✅ Avoid empty updates
    
        // ✅ Compare with existing gridRows to prevent unnecessary updates
        if (JSON.stringify(updatedRows) === JSON.stringify(gridRows)) return;
    
        setGridRows(updatedRows);
    
        // ✅ Maintain Undo/Redo History immutably
        setHistory((prevHistory) => [
            ...prevHistory.slice(0, historyIndex + 1),
            { rows: updatedRows, columns: gridColumns },
        ]);
        
        setHistoryIndex((prevIndex) => prevIndex + 1);
    };
    

    /** ✅ Column Reduction */
    const applyColumnReduction = (colKey, factor) => {
        const newRows = gridRows.map(row => {
            const value = row[colKey];
            const numericValue = typeof value === 'string' ? parseFloat(value.replace(/,/g, '')) : value;
            const originalValue = typeof value === 'number' ? value : numericValue;
            const reducedValue = !isNaN(numericValue) ? (originalValue / factor).toFixed(2) : value;
            return {
                ...row,
                [colKey]: typeof reducedValue === 'number' ? reducedValue.toLocaleString() : reducedValue
            };
        });

        const newColumns = gridColumns.map(col =>
            col.key === colKey ? { ...col, name: `${col.name} x${factor}` } : col
        );

        setGridRows(newRows);
        setGridColumns(newColumns);
        setColumnReduction({ ...columnReduction, [colKey]: factor });

        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push({ rows: newRows, columns: newColumns });
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
    };

    /** ✅ Undo & Redo */
    const undo = () => {
        if (historyIndex > 0) {
            setHistoryIndex(historyIndex - 1);
            setGridRows(history[historyIndex - 1].rows);
            setGridColumns(history[historyIndex - 1].columns);
        }
    };

    const redo = () => {
        if (historyIndex < history.length - 1) {
            setHistoryIndex(historyIndex + 1);
            setGridRows(history[historyIndex + 1].rows);
            setGridColumns(history[historyIndex + 1].columns);
        }
    };

    const handleColumnReset = (colKey) => {
        setGridColumns((prevColumns) => {
            const newColumns = prevColumns.map(col =>
                col.key === colKey ? { ...col, width: 200 } : col
            );
    
            // ✅ Store in history for Undo/Redo
            setHistory((prevHistory) => [
                ...prevHistory.slice(0, historyIndex + 1),
                { rows: gridRows, columns: newColumns },
            ]);
            setHistoryIndex((prevIndex) => prevIndex + 1);
    
            return newColumns;
        });
    };
    
    

    /** ✅ Reset to Original Data */
    const resetFileContent = () => {
        if (originalData.file === selectedFile && originalData.sheet === selectedSheet) {
            setGridRows(originalData.rows);
            setGridColumns(originalData.columns);
            setColumnReduction({});
            setHistory([{ rows: originalData.rows, columns: originalData.columns }]);
            setHistoryIndex(0);
        }
    };

    /** ✅ Download the Updated Excel File */
    const downloadUpdatedExcel = () => {
        if (!selectedFile || !selectedSheet) return;

        const worksheet = XLSX.utils.json_to_sheet(gridRows.map(row => {
            const formattedRow = {};
            gridColumns.forEach(col => {
                formattedRow[col.name] = row[col.key];
            });
            return formattedRow;
        }));

        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, selectedSheet);

        XLSX.writeFile(workbook, `${selectedFile}-updated.xlsx`);
    };

    return (
        <div className="beta-excel-container">
            <h3>Excel Review & Editing</h3>

            {/* File Selection */}
            <div className='selection-container'>
                <label htmlFor="file-select">Select File:</label>
                <select 
                    id="file-select" 
                    onChange={(e) => handleFileSelection(e.target.value)} 
                    value={selectedFile} 
                    disabled={excelFiles.length === 0}
                >
                    {excelFiles.length > 0 ? (
                        excelFiles.map((file) => (
                            <option key={file.name} value={file.name}>{file.name.split('/').pop()}</option>
                        ))
                    ) : (
                        <option value="">No files available</option>
                    )}
                </select>

                {/* ✅ Select Sheet */}
                <label htmlFor="sheet-select">Select Sheet:</label>
                <select 
                    id="sheet-select" 
                    onChange={(e) => handleSheetSelection(e.target.value)} 
                    value={selectedSheet}
                >
                    {sheetNames[selectedFile]?.map((sheet) => (
                        <option key={sheet} value={sheet}>{sheet}</option>
                    ))}
                </select>

                {/* Column Reduction UI */}
                {/* ✅ Select Column to Reduce */}
                <label htmlFor="column-select">Select Column to Reduce:</label>
                <select 
                    id="column-select" 
                    onChange={(e) => setSelectedColumn(e.target.value)} 
                    value={selectedColumn}
                    >
                    <option value="">Select Column</option>
                    {gridColumns.map((col) => (
                        <option key={col.key} value={col.key}>{col.name}</option>
                    ))}
                </select>

                {/* ✅ Reduction Factor Input */}
                <label htmlFor="reduction-factor">Reduction Factor:</label>
                <input 
                    id="reduction-factor"
                    type="number"
                    value={reductionFactor}
                    onChange={(e) => setReductionFactor(Number(e.target.value))}
                    min="1"
                    step="0.1"
                    />
                </div>

                {/* ✅ Apply Reduction Button */}
                <button 
                    className="apply-reduction-btn"
                    onClick={() => applyColumnReduction(selectedColumn, reductionFactor)} 
                    disabled={!selectedColumn || reductionFactor <= 0}
                    >
                    APPLY REDUCTION
                </button>

            {/* Action Buttons - with Icons */}
            <div className="action-buttons">
                <button onClick={undo} title="Undo">
                <FaUndo /> Undo
                </button>
                <button onClick={redo} title="Redo">
                <FaRedo /> Redo
                </button>
                <button onClick={resetFileContent} title="Reset">
                <FaSyncAlt /> Reset
                </button>
                <button onClick={downloadUpdatedExcel} title="Download Excel" disabled={gridRows.length === 0}>
                <FaDownload /> Download
                </button>
            </div>

            {/* Data Grid */}
            <div className="excel-table-container">
                {gridRows.length > 0 && gridColumns.length > 0 ? (
                    <div className="table-wrapper">
                        <DataGrid
                            columns={gridColumns}
                            rows={gridRows}
                            onRowsChange={handleGridChange} // ✅ Handles Grid Changes
                            className="react-data-grid excel-table"
                            style={{ minHeight: "400px", width: "100%" }}
                            rowHeight={35}
                            headerRowHeight={40}
                            editable
                        />
                    </div>
                ) : (
                    <p>No data available. Please select an Excel file.</p>
                )}
            </div>

        </div>
    );
};

export default BetaExcelView;
