import 'react-data-grid/lib/styles.css';
import React, { useState, useEffect, useCallback, useRef } from 'react';
import * as XLSX from 'xlsx';
import DataGrid from 'react-data-grid';
import ExcelEditTools from './ExcelEditorTools';
import './styles/BetaExcelView.css';

const BetaExcelView = ({ extractedData }) => {
    const [excelFiles, setExcelFiles] = useState([]);
    const [selectedFile, setSelectedFile] = useState("");
    const [selectedSheet, setSelectedSheet] = useState("");
    const [sheetNames, setSheetNames] = useState({});
    const [gridRows, setGridRows] = useState([]);
    const [gridColumns, setGridColumns] = useState([]);
    const [originalData, setOriginalData] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [alignment, setAlignment] = useState('center');
    const [editingColumn, setEditingColumn] = useState(null);
    const [tempColumnName, setTempColumnName] = useState('');
    const [selectedCell, setSelectedCell] = useState(null);

    const downloadedFilesRef = useRef(new Set());
    const gridRef = useRef(null);

    // Generate unique ID for new rows
    const generateId = () => Math.max(0, ...gridRows.map(row => row.id)) + 1;

    // Function to handle column name updates
    const handleColumnHeaderClick = (columnKey, currentName) => {
        setEditingColumn(columnKey);
        setTempColumnName(currentName);
    };

    const handleColumnNameChange = (e) => {
        setTempColumnName(e.target.value);
    };

    const saveColumnName = async (columnKey) => {
        if (!tempColumnName.trim()) {
            alert('Column name cannot be empty');
            return;
        }

        try {
            setIsLoading(true);
            const columnIndex = gridColumns.findIndex(col => col.key === columnKey);
            
            const response = await fetch('/excel/update-column-name', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    column_index: columnIndex,
                    new_name: tempColumnName
                })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to update column name');
            }

            setGridColumns(prevColumns => 
                prevColumns.map(col => 
                    col.key === columnKey ? { ...col, name: tempColumnName } : col
                )
            );
            
            setEditingColumn(null);
        } catch (error) {
            console.error('Error updating column name:', error);
            alert(`Error updating column name: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const getColumns = () => {
        const columns = gridColumns.map(col => ({
            ...col,
            renderHeaderCell: () => (
                <div 
                    style={{ 
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        padding: '0 8px',
                        cursor: 'pointer'
                    }}
                    onClick={() => handleColumnHeaderClick(col.key, col.name)}
                >
                    {editingColumn === col.key ? (
                        <input
                            type="text"
                            value={tempColumnName}
                            onChange={handleColumnNameChange}
                            onBlur={() => saveColumnName(col.key)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    saveColumnName(col.key);
                                } else if (e.key === 'Escape') {
                                    setEditingColumn(null);
                                }
                            }}
                            autoFocus
                            style={{
                                width: '100%',
                                border: '2px solid #2684FF',
                                padding: '4px',
                                fontSize: 'inherit',
                                fontFamily: 'inherit',
                                outline: 'none'
                            }}
                        />
                    ) : (
                        <div style={{ width: '100%' }}>{col.name}</div>
                    )}
                </div>
            ),
            renderCell: ({ row, column }) => (
                <div style={{ textAlign: alignment }}>
                    {row[column.key] || ''}
                </div>
            ),
            editor: ({ row, onRowChange, column }) => (
                <input
                    type="text"
                    value={row[column.key] || ''}
                    onChange={(e) => onRowChange({ ...row, [column.key]: e.target.value })}
                    autoFocus
                    style={{ textAlign: alignment }}
                />
            )
        }));

        return columns;
    };

    // Load sheet data
    const loadSheetData = useCallback(async (file, sheet) => {
        try {
            setIsLoading(true);
            const excelFile = excelFiles.find(f => f.name === file);
            if (!excelFile) return;

            const worksheet = excelFile.workbook.Sheets[sheet];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: false });

            const dataColumns = jsonData[0]?.map((col, index) => ({
                key: `col-${index}`,
                name: col?.toString().trim() || `Column ${index + 1}`,
                editable: true,
                width: 200,
                resizable: true,
                idx: index,
                renderCell: ({ row, column }) => (
                    <div style={{ textAlign: alignment }}>
                        {row[column.key] || ''}
                    </div>
                ),
                editor: ({ row, onRowChange, column }) => (
                    <input
                        type="text"
                        value={row[column.key] || ''}
                        onChange={(e) => onRowChange({ ...row, [column.key]: e.target.value })}
                        autoFocus
                        style={{ textAlign: alignment }}
                    />
                )
            })) || [];

            const rows = jsonData.slice(1).map((row, rowIndex) => {
                const rowData = { id: rowIndex + 1 };
                dataColumns.forEach((col, colIndex) => {
                    rowData[col.key] = row[colIndex] !== undefined ? row[colIndex] : "";
                });
                return rowData;
            });

            setGridColumns(dataColumns);
            setGridRows(rows);
            setOriginalData({ file, sheet, rows, columns: dataColumns });
        } catch (error) {
            console.error(`Error loading sheet data:`, error);
        } finally {
            setIsLoading(false);
        }
    }, [excelFiles, alignment]);

    // Download and load Excel files
    const downloadAndLoadExcels = useCallback(async (excelPaths, filesToDownload) => {
        try {
            setIsLoading(true);
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
        } catch (error) {
            console.error('Error downloading and loading Excel files:', error);
        } finally {
            setIsLoading(false);
        }
    }, [excelFiles, sheetNames, selectedFile, loadSheetData]);

    // Process extracted data
    useEffect(() => {
        if (extractedData) {
            const allExcelPaths = [
                ...new Set([
                    ...Object.values(extractedData.excel_paths || {}),
                    ...Object.values(extractedData.combined_excel_paths || {})
                ])
            ];

            const newFilesToDownload = allExcelPaths
                .map((path) => path.split('/').pop())
                .filter((fileName) => !downloadedFilesRef.current.has(fileName));

            if (newFilesToDownload.length > 0) {
                downloadAndLoadExcels(extractedData.excel_paths, newFilesToDownload);
                newFilesToDownload.forEach((fileName) => downloadedFilesRef.current.add(fileName));
            }
        }
    }, [extractedData, downloadAndLoadExcels]);

    // Handle file selection
    const handleFileSelection = (fileName) => {
        setSelectedFile(fileName);
        if (sheetNames[fileName]?.length > 0) {
            setSelectedSheet(sheetNames[fileName][0]);
            loadSheetData(fileName, sheetNames[fileName][0]);
        }
    };

    // Handle sheet selection
    const handleSheetSelection = (sheetName) => {
        setSelectedSheet(sheetName);
        loadSheetData(selectedFile, sheetName);
    };

    return (
        <div className="beta-excel-container">
            <h3>Excel Review & Editing</h3>

            {isLoading && <div className="loading-overlay">Loading...</div>}

            {/* File Selection */}
            <div className='selection-container'>
                <label htmlFor="file-select">Select File:</label>
                <select 
                    id="file-select" 
                    onChange={(e) => handleFileSelection(e.target.value)} 
                    value={selectedFile} 
                    disabled={excelFiles.length === 0 || isLoading}
                >
                    {excelFiles.length > 0 ? (
                        excelFiles.map((file) => (
                            <option key={file.name} value={file.name}>{file.name.split('/').pop()}</option>
                        ))
                    ) : (
                        <option value="">No files available</option>
                    )}
                </select>

                {/* Select Sheet */}
                <label htmlFor="sheet-select">Select Sheet:</label>
                <select 
                    id="sheet-select" 
                    onChange={(e) => handleSheetSelection(e.target.value)} 
                    value={selectedSheet}
                    disabled={isLoading}
                >
                    {sheetNames[selectedFile]?.map((sheet) => (
                        <option key={sheet} value={sheet}>{sheet}</option>
                    ))}
                </select>
            </div>

            {/* Excel Edit Tools */}
            <ExcelEditTools 
                selectedFile={selectedFile}
                selectedSheet={selectedSheet}
                gridRows={gridRows}
                setGridRows={setGridRows}
                gridColumns={gridColumns}
                setGridColumns={setGridColumns}
                isLoading={isLoading}
                setIsLoading={setIsLoading}
                alignment={alignment}
                setAlignment={setAlignment}
                generateId={generateId}
                originalData={originalData}
                loadSheetData={loadSheetData}
                selectedCell={selectedCell}
            />

            {/* Data Grid */}
            <div className="excel-table-container">
                {gridRows.length > 0 && gridColumns.length > 0 ? (
                    <DataGrid
                        ref={gridRef}
                        columns={getColumns()}
                        rows={gridRows}
                        onRowsChange={(newRows, { indexes, column }) => {
                            setGridRows(newRows);
                        }}
                        onCellClick={(args) => setSelectedCell({
                            rowIdx: args.rowIdx,
                            columnIdx: args.column.idx,
                            columnKey: args.column.key
                        })}
                        className="react-data-grid excel-table"
                        style={{ minHeight: "400px", width: "100%" }}
                        rowHeight={35}
                        headerRowHeight={40}
                        rowKeyGetter={row => row.id}
                    />
                ) : (
                    <p>No data available. Please select an Excel file.</p>
                )}
            </div>
        </div>
    );
};

export default BetaExcelView;