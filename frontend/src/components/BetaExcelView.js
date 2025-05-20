import 'react-data-grid/lib/styles.css';
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaUndo, FaRedo, FaDownload, FaSyncAlt, FaPlus, FaAlignLeft, FaAlignCenter, FaAlignRight, FaObjectGroup, FaTrash } from "react-icons/fa";
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
    const [alignment, setAlignment] = useState('center');
    const [mergeMode, setMergeMode] = useState(false);
    const [selectedCells, setSelectedCells] = useState([]);
    const [dragRow, setDragRow] = useState(null);
    const [dragColumn, setDragColumn] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [editingColumn, setEditingColumn] = useState(null);


    const downloadedFilesRef = useRef(new Set());
    const gridRef = useRef(null);

    // Generate unique ID for new rows
    const generateId = () => Math.max(0, ...gridRows.map(row => row.id)) + 1;

    // Function to handle column name updates

    const [tempColumnName, setTempColumnName] = useState('');

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

        // Update the gridColumns state with the new name
        setGridColumns(prevColumns => 
        prevColumns.map(col => 
            col.key === columnKey ? { ...col, name: tempColumnName } : col
        )
        );
        
        setEditingColumn(null);
        saveToHistory();
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

    columns.push({
        key: 'actions',
        name: 'Actions',
        width: 100,
        renderCell: ({ row }) => (
        <button 
            onClick={() => handleDeleteRow(row.id)} 
            className="delete-row-btn"
            disabled={isLoading}
        >
            <FaTrash />
        </button>
        ),
        renderHeaderCell: () => 'Actions',
        editable: false
    });

    return columns;
    };

    // Enhanced formula calculation
    const calculateFormula = (formula, rows, currentRowId, currentColKey) => {
        try {
            // Basic arithmetic operations
            if (/^=(\d+\.?\d*)\s*([+\-*/%])\s*(\d+\.?\d*)$/.test(formula)) {
                const [, num1, op, num2] = formula.match(/^=(\d+\.?\d*)\s*([+\-*/%])\s*(\d+\.?\d*)$/);
                const n1 = parseFloat(num1);
                const n2 = parseFloat(num2);
                
                switch(op) {
                    case '+': return n1 + n2;
                    case '-': return n1 - n2;
                    case '*': return n1 * n2;
                    case '/': return n2 !== 0 ? n1 / n2 : '#DIV/0!';
                    case '%': return n1 % n2;
                    default: return formula;
                }
            }
            
            // Percentage
            if (/^=\d+\.?\d*%$/.test(formula)) {
                return parseFloat(formula.slice(1, -1)) / 100;
            }
            
            // Sum of range (e.g., =SUM(A1:A5))
            if (/^=SUM\([A-Za-z]+\d+:[A-Za-z]+\d+\)$/.test(formula)) {
                const range = formula.match(/=SUM\(([^)]+)\)/)[1];
                const [start, end] = range.split(':');
                // Implement range sum logic here
                return "100"; // Placeholder
            }
            
            return formula; // Return as-is if not a recognized formula
        } catch (e) {
            return `#ERROR: ${e.message}`;
        }
    };

    // Helper function to convert column index to Excel-style letters
    const getExcelColumnName = (index) => {
        let colName = '';
        while (index >= 0) {
            colName = String.fromCharCode((index % 26) + 65) + colName;
            index = Math.floor(index / 26) - 1;
        }
        return colName;
    };

    // Save current state to history
    const saveToHistory = useCallback(() => {
        const currentState = {
            rows: [...gridRows],
            columns: [...gridColumns]
        };

        setHistory(prev => {
            const newHistory = prev.slice(0, historyIndex + 1);
            newHistory.push(currentState);
            return newHistory;
        });
        setHistoryIndex(prev => prev + 1);
    }, [gridRows, gridColumns, historyIndex]);

    // Handle cell editing with formula support
    const handleCellEdit = async (updatedRows, { indexes, column }) => {
        const rowIndex = indexes[0];
        const newValue = updatedRows[rowIndex][column.key];

        try {
            const columnLetter = getExcelColumnName(column.idx);
            const cellRef = `${columnLetter}${rowIndex + 2}`;

            const response = await fetch('/excel/update-cell', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    cell_ref: cellRef,
                    new_value: newValue
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update cell');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Failed to update cell');
            }

            setGridRows(prevRows => {
                const newRows = [...prevRows];
                newRows[rowIndex] = {
                    ...newRows[rowIndex],
                    [column.key]: newValue.startsWith('=') ? 
                        { raw: newValue, computed: calculateFormula(newValue, prevRows, newRows[rowIndex].id, column.key) } : 
                        newValue
                };
                return newRows;
            });

            saveToHistory();

        } catch (error) {
            console.error('Error updating cell:', error);
            // Revert to previous value
            setGridRows(prevRows => [...prevRows]);
        }
    };

    // Add New Column
    const addNewColumn = async () => {
        try {
            setIsLoading(true);
            const response = await fetch('/excel/add-column', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    column_name: `Column ${gridColumns.length + 1}`,
                    sheet: selectedSheet
                })
            });

            // First check if the response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Invalid response: ${text.substring(0, 100)}`);
            }

            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to add column');
            }

            // Manually add the new column to the UI
            const newColumn = {
                key: `col-${gridColumns.length}`,
                name: data.column_name,
                editable: true,
                width: 200,
                resizable: true,
                idx: gridColumns.length,
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
            };

            setGridColumns([...gridColumns, newColumn]);
            setGridRows(prevRows => 
                prevRows.map(row => ({
                    ...row,
                    [newColumn.key]: ""
                }))
            );
            saveToHistory();

        } catch (error) {
            console.error('Error adding column:', error);
            alert(`Error adding column: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Add new row with immediate UI update
    const addNewRow = async () => {
        try {
            setIsLoading(true);
            const response = await fetch('/excel/add-row', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    sheet: selectedSheet
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Failed to add row');
            }

            // Create a new empty row
            const newRow = { id: generateId() };
            gridColumns.forEach(col => {
                newRow[col.key] = "";
            });

            // Update state
            setGridRows(prevRows => [...prevRows, newRow]);
            saveToHistory();

        } catch (error) {
            console.error('Error adding row:', error);
            alert(`Error adding row: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle row reordering via drag and drop
    const handleRowReorder = (sourceIndex, targetIndex) => {
        const newRows = [...gridRows];
        const [movedRow] = newRows.splice(sourceIndex, 1);
        newRows.splice(targetIndex, 0, movedRow);

        setGridRows(newRows);
        saveToHistory();
    };

    // Handle column reordering
    const handleColumnReorder = (sourceKey, targetKey) => {
        const sourceIndex = gridColumns.findIndex(col => col.key === sourceKey);
        const targetIndex = gridColumns.findIndex(col => col.key === targetKey);

        if (sourceIndex === -1 || targetIndex === -1 || sourceIndex === targetIndex) return;

        const newColumns = [...gridColumns];
        const [movedColumn] = newColumns.splice(sourceIndex, 1);
        newColumns.splice(targetIndex, 0, movedColumn);

        setGridColumns(newColumns);
        saveToHistory();
    };

    // Merge selected cells
    const mergeSelectedCells = async () => {
        if (selectedCells.length < 2) return;

        try {
            setIsLoading(true);
            const firstCell = selectedCells[0];
            const lastCell = selectedCells[selectedCells.length - 1];
            const rangeRef = `${String.fromCharCode(65 + firstCell.columnIdx)}${firstCell.rowIdx + 2}:${
                String.fromCharCode(65 + lastCell.columnIdx)}${lastCell.rowIdx + 2}`;
            
            const mergedValue = gridRows[firstCell.rowIdx][gridColumns[firstCell.columnIdx].key];

            const response = await fetch('/excel/merge-cells', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    range_ref: rangeRef,
                    merge_value: mergedValue,
                    sheet: selectedSheet
                })
            });

            if (!response.ok) {
                throw new Error('Failed to merge cells');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Failed to merge cells');
            }

            // Refresh data after successful merge
            await loadSheetData(selectedFile, selectedSheet);
            setSelectedCells([]);
            setMergeMode(false);
            saveToHistory();

        } catch (error) {
            console.error('Error merging cells:', error);
            alert(`Error merging cells: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle delete row
    const handleDeleteRow = async (rowId) => {
        try {
            setIsLoading(true);
            const rowIndex = gridRows.findIndex(row => row.id === rowId);
            if (rowIndex === -1) return;

            const response = await fetch('/excel/delete-rows', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    rows: [rowIndex + 2]  // +2 because Excel is 1-based and we have header row
                })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to delete row');
            }

            // Refresh data after successful deletion
            await loadSheetData(selectedFile, selectedSheet);
            saveToHistory();
        } catch (error) {
            console.error('Error deleting row:', error);
            alert(`Error deleting row: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Alignment functions
    const handleAlignLeft = () => {
        setAlignment('left');
        saveToHistory();
    };
    const handleAlignCenter = () => {
        setAlignment('center');
        saveToHistory();
    };
    const handleAlignRight = () => {
        setAlignment('right');
        saveToHistory();
    };

    // Handle drag and drop for rows
    const handleRowDrop = (targetRowId) => {
        if (!dragRow) return;
        
        const sourceIndex = gridRows.findIndex(row => row.id === dragRow);
        const targetIndex = gridRows.findIndex(row => row.id === targetRowId);
        
        if (sourceIndex !== -1 && targetIndex !== -1 && sourceIndex !== targetIndex) {
            handleRowReorder(sourceIndex, targetIndex);
        }
    };

    // Handle drag and drop for columns
    const handleColumnDrop = (targetColumnKey) => {
        if (!dragColumn) return;
        
        const sourceKey = dragColumn;
        const targetKey = targetColumnKey;
        
        if (sourceKey && targetKey && sourceKey !== targetKey) {
            handleColumnReorder(sourceKey, targetKey);
        }
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
                    <div 
                        style={{ textAlign: alignment }}
                        onMouseDown={() => setDragRow(row.id)}
                        onMouseUp={() => setDragRow(null)}
                    >
                        {typeof row[column.key] === 'object' ? 
                            row[column.key]?.computed || row[column.key]?.raw || '' : 
                            row[column.key] || ''}
                    </div>
                ),
                renderHeaderCell: ({ column }) => (
                    <div
                        style={{ cursor: 'move' }}
                        onMouseDown={() => setDragColumn(column.key)}
                        onMouseUp={() => setDragColumn(null)}
                        onMouseOver={() => setDragColumn(column.key)}
                        onMouseOut={() => setDragColumn(null)}
                    >
                        {column.name}
                    </div>
                ),
                editor: ({ row, onRowChange, column }) => (
                    <input
                        type="text"
                        value={typeof row[column.key] === 'object' ? row[column.key]?.raw || '' : row[column.key] || ''}
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
            setHistory([{ rows, columns: dataColumns }]);
            setHistoryIndex(0);
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

    // Column reduction
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
        saveToHistory();
    };

    // Undo & Redo
    const undo = () => {
        if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            setHistoryIndex(newIndex);
            setGridRows([...history[newIndex].rows]);
            setGridColumns([...history[newIndex].columns]);
        }
    };

    const redo = () => {
        if (historyIndex < history.length - 1) {
            const newIndex = historyIndex + 1;
            setHistoryIndex(newIndex);
            setGridRows([...history[newIndex].rows]);
            setGridColumns([...history[newIndex].columns]);
        }
    };

    // Reset to original data
    const resetFileContent = () => {
        if (originalData.file === selectedFile && originalData.sheet === selectedSheet) {
            setGridRows(originalData.rows);
            setGridColumns(originalData.columns);
            setColumnReduction({});
            setHistory([{ rows: originalData.rows, columns: originalData.columns }]);
            setHistoryIndex(0);
        }
    };

    // Download the updated Excel file
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

        XLSX.writeFile(workbook, `${selectedFile.split('/').pop()}-updated.xlsx`);
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

                {/* Column Reduction UI */}
                <label htmlFor="column-select">Select Column to Reduce:</label>
                <select 
                    id="column-select" 
                    onChange={(e) => setSelectedColumn(e.target.value)} 
                    value={selectedColumn}
                    disabled={isLoading}
                >
                    <option value="">Select Column</option>
                    {gridColumns.map((col) => (
                        col.key !== 'actions' && <option key={col.key} value={col.key}>{col.name}</option>
                    ))}
                </select>

                {/* Reduction Factor Input */}
                <label htmlFor="reduction-factor">Reduction Factor:</label>
                <input 
                    id="reduction-factor"
                    type="number"
                    value={reductionFactor}
                    onChange={(e) => setReductionFactor(Number(e.target.value))}
                    min="1"
                    step="0.1"
                    disabled={isLoading}
                />
            </div>

            {/* Apply Reduction Button */}
            <button 
                className="apply-reduction-btn"
                onClick={() => applyColumnReduction(selectedColumn, reductionFactor)} 
                disabled={!selectedColumn || reductionFactor <= 0 || isLoading}
            >
                APPLY REDUCTION
            </button>

            {/* Action Buttons */}
            <div className="action-buttons">
                <button onClick={undo} title="Undo" disabled={historyIndex <= 0 || isLoading}>
                    <FaUndo /> Undo
                </button>
                <button onClick={redo} title="Redo" disabled={historyIndex >= history.length - 1 || isLoading}>
                    <FaRedo /> Redo
                </button>
                <button onClick={addNewColumn} title="Add Column" disabled={isLoading}>
                    <FaPlus /> Add Column
                </button>
                <button onClick={addNewRow} title="Add Row" disabled={isLoading}>
                    <FaPlus /> Add Row
                </button>
                <button onClick={resetFileContent} title="Reset" disabled={isLoading}>
                    <FaSyncAlt /> Reset
                </button>
                <button onClick={downloadUpdatedExcel} title="Download Excel" disabled={gridRows.length === 0 || isLoading}>
                    <FaDownload /> Download
                </button>
                <div className="alignment-buttons">
                    <button onClick={handleAlignLeft} title="Align Left" disabled={isLoading}>
                        <FaAlignLeft />
                    </button>
                    <button onClick={handleAlignCenter} title="Align Center" disabled={isLoading}>
                        <FaAlignCenter />
                    </button>
                    <button onClick={handleAlignRight} title="Align Right" disabled={isLoading}>
                        <FaAlignRight />
                    </button>
                </div>
                <button 
                    onClick={() => setMergeMode(!mergeMode)} 
                    className={mergeMode ? 'active-mode' : ''}
                    title="Merge Cells"
                    disabled={isLoading}
                >
                    <FaObjectGroup /> {mergeMode ? 'Cancel Merge' : 'Merge Mode'}
                </button>
                {mergeMode && (
                    <button onClick={mergeSelectedCells} title="Merge Selected" disabled={selectedCells.length < 2 || isLoading}>
                        <FaObjectGroup /> Merge Selected
                    </button>
                )}
            </div>

            {mergeMode && (
                <div className="merge-notice">
                    {selectedCells.length > 0 
                        ? `${selectedCells.length} cell(s) selected` 
                        : "Select cells to merge"}
                </div>
            )}

            {/* Data Grid */}
            <div className="excel-table-container">
                {gridRows.length > 0 && gridColumns.length > 0 ? (
                    <DataGrid
                        ref={gridRef}
                        columns={getColumns()}
                        rows={gridRows}
                        onRowsChange={(newRows, { indexes, column }) => {
                            setGridRows(newRows);
                            if (column && column.key !== 'actions') {
                            handleCellEdit(newRows, { indexes, column });
                            }
                        }}
                        className="react-data-grid excel-table"
                        style={{ minHeight: "400px", width: "100%" }}
                        rowHeight={35}
                        headerRowHeight={40}
                        rowKeyGetter={row => row.id}
                        onRowClick={(row) => {
                            if (mergeMode) {
                            const rowIndex = gridRows.findIndex(r => r.id === row.id);
                            const columnKey = Object.keys(row).find(key => key !== 'id' && key !== 'actions');
                            const columnIndex = gridColumns.findIndex(col => col.key === columnKey);
                            
                            if (columnIndex !== -1) {
                                setSelectedCells(prev => [...prev, {
                                rowIdx: rowIndex,
                                columnIdx: columnIndex,
                                columnKey: columnKey
                                }]);
                            }
                            }
                        }}
                        rowClass={row => 
                            `${dragRow === row.id ? 'dragging-row' : ''} 
                            ${selectedCells.some(c => gridRows[c.rowIdx]?.id === row.id) ? 'selected-cell' : ''}`
                        }
                        onRowDragOver={(row) => handleRowDrop(row.id)}
                        onHeaderDrop={(column) => handleColumnDrop(column.key)}
                        />
                ) : (
                    <p>No data available. Please select an Excel file.</p>
                )}
            </div>
        </div>
    );
};

export default BetaExcelView;