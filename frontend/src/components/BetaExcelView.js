import 'react-data-grid/lib/styles.css';
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaUndo, FaRedo, FaDownload, FaSyncAlt, FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaObjectGroup } from "react-icons/fa";
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
    const [selectionRange, setSelectionRange] = useState(null);
    const [mergedCells, setMergedCells] = useState([]);
    const [selectedRows, setSelectedRows] = useState(new Set());
    const [isSelecting, setIsSelecting] = useState(false);
    const [editingRow, setEditingRow] = useState(null);

    const downloadedFilesRef = useRef(new Set());
    const gridRef = useRef();

    // Helper function to update history
    const updateHistory = useCallback((rows, columns) => {
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push({ rows, columns });
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
    }, [history, historyIndex]);

    // Handle cell selection
    const handleCellSelect = useCallback((rowIdx, columnKey) => {
        const colIdx = gridColumns.findIndex(col => col.key === columnKey);
        
        if (!selectionRange) {
            setSelectionRange({
                start: { row: rowIdx, col: colIdx },
                end: { row: rowIdx, col: colIdx }
            });
            setIsSelecting(true);
        } else if (isSelecting) {
            setSelectionRange(prev => ({
                ...prev,
                end: { row: rowIdx, col: colIdx }
            }));
        }
    }, [gridColumns, selectionRange, isSelecting]);

    // Handle mouse up to finish selection
    const handleMouseUp = useCallback(() => {
        setIsSelecting(false);
    }, []);

    // Enhanced formula evaluation
    const evaluateFormula = (formula, rows, currentRowId, columns) => {
        try {
            // Replace cell references (A1, B2, etc.) with their values
            const evaluated = formula.replace(/([A-Z]+)(\d+)/g, (match, colLetters, rowNum) => {
                // Convert column letters to index (A=0, B=1, etc.)
                let colIndex = 0;
                for (let i = 0; i < colLetters.length; i++) {
                    colIndex = colIndex * 26 + (colLetters.charCodeAt(i) - 64);
                }
                colIndex--; // A should be 0, not 1
                
                const targetRow = rows.find(r => r.id === parseInt(rowNum) - 1);
                const columnKey = columns[colIndex]?.key;
                
                if (targetRow && columnKey) {
                    const value = targetRow[columnKey];
                    // Remove any non-numeric characters except decimal point
                    return value ? value.toString().replace(/[^0-9.-]/g, '') : '0';
                }
                return '0';
            });
            
            // Evaluate the formula safely
            return new Function('return ' + evaluated)();
        } catch (e) {
            console.error("Formula error:", e);
            return formula; // Return original formula if evaluation fails
        }
    };

    // Handle cell editing with improved formula support
    const handleCellEdit = useCallback((rowId, columnKey, newValue) => {
        setGridRows(prevRows => {
            const updatedRows = prevRows.map(row => 
                row.id === rowId ? { ...row, [columnKey]: newValue } : row
            );

            // Formula evaluation
            if (newValue.startsWith('=')) {
                try {
                    const result = evaluateFormula(
                        newValue.slice(1),
                        updatedRows,
                        rowId,
                        gridColumns
                    );
                    updatedRows.find(row => row.id === rowId)[columnKey] = result;
                } catch (e) {
                    console.error("Formula error:", e);
                }
            }

            updateHistory(updatedRows, gridColumns);
            return updatedRows;
        });
    }, [gridColumns, updateHistory]);

    // Add new row
    const addNewRow = useCallback(() => {
        const newRow = { id: gridRows.length > 0 ? Math.max(...gridRows.map(r => r.id)) + 1 : 0 };
        gridColumns.forEach(col => {
            if (col.key !== 'actions') {
                newRow[col.key] = "";
            }
        });
        
        const updatedRows = [...gridRows, newRow];
        setGridRows(updatedRows);
        updateHistory(updatedRows, gridColumns);
    }, [gridRows, gridColumns, updateHistory]);

    // Delete row
    const deleteRow = useCallback((rowId) => {
        const updatedRows = gridRows.filter(row => row.id !== rowId);
        setGridRows(updatedRows);
        updateHistory(updatedRows, gridColumns);
    }, [gridRows, gridColumns, updateHistory]);

    // Toggle row editing
    const toggleRowEdit = useCallback((rowId) => {
        setEditingRow(editingRow === rowId ? null : rowId);
    }, [editingRow]);

    // Save edited row
    const saveRowEdit = useCallback((row) => {
        setEditingRow(null);
        setGridRows(prevRows => {
            const updatedRows = prevRows.map(r => r.id === row.id ? row : r);
            updateHistory(updatedRows, gridColumns);
            return updatedRows;
        });
    }, [gridColumns, updateHistory]);

    // Cancel row editing
    const cancelRowEdit = useCallback(() => {
        setEditingRow(null);
    }, []);

    // Add new column
    const addNewColumn = useCallback(() => {
        const newColKey = `col-${gridColumns.length - 1}`; // Subtract 1 to account for actions column
        const newColumn = {
            key: newColKey,
            name: String.fromCharCode(65 + gridColumns.length - 2), // Adjust for actions column
            editable: true,
            width: 120,
            resizable: true,
            renderCell: ({ row, onRowChange }) => (
                <div 
                    onClick={() => handleCellSelect(row.id, newColKey)}
                    onMouseDown={() => handleCellSelect(row.id, newColKey)}
                    onMouseEnter={() => isSelecting && handleCellSelect(row.id, newColKey)}
                    style={{ width: '100%', height: '100%' }}
                >
                    <input
                        type="text"
                        value={row[newColKey] || ""}
                        onChange={(e) => {
                            onRowChange({ ...row, [newColKey]: e.target.value });
                            handleCellEdit(row.id, newColKey, e.target.value);
                        }}
                        style={{ width: '100%', border: 'none', background: 'transparent' }}
                    />
                </div>
            )
        };

        // Insert before actions column
        const actionColIndex = gridColumns.findIndex(col => col.key === 'actions');
        const updatedColumns = [
            ...gridColumns.slice(0, actionColIndex),
            newColumn,
            ...gridColumns.slice(actionColIndex)
        ];

        const updatedRows = gridRows.map(row => ({
            ...row,
            [newColKey]: ""
        }));

        setGridColumns(updatedColumns);
        setGridRows(updatedRows);
        updateHistory(updatedRows, updatedColumns);
    }, [gridRows, gridColumns, updateHistory, handleCellSelect, isSelecting, handleCellEdit]);

    // Delete selected column
    const deleteSelectedColumn = useCallback(() => {
        if (!selectedColumn) return;
        
        const updatedColumns = gridColumns.filter(col => col.key !== selectedColumn);
        const updatedRows = gridRows.map(row => {
            const newRow = {...row};
            delete newRow[selectedColumn];
            return newRow;
        });

        setGridColumns(updatedColumns);
        setGridRows(updatedRows);
        setSelectedColumn("");
        updateHistory(updatedRows, updatedColumns);
    }, [selectedColumn, gridRows, gridColumns, updateHistory]);

    // Merge cells functionality
    const handleMergeCells = useCallback(() => {
        if (!selectionRange) return;
        
        const { start, end } = selectionRange;
        const newMergedCells = [...mergedCells, { 
            start: { 
                row: Math.min(start.row, end.row), 
                col: Math.min(start.col, end.col) 
            }, 
            end: { 
                row: Math.max(start.row, end.row), 
                col: Math.max(start.col, end.col) 
            } 
        }];
        setMergedCells(newMergedCells);
        setSelectionRange(null);
    }, [selectionRange, mergedCells]);

    // Unmerge cells
    const handleUnmergeCells = useCallback(() => {
        if (!selectionRange) return;
        
        const { start } = selectionRange;
        const newMergedCells = mergedCells.filter(merge => 
            !(merge.start.row === start.row && merge.start.col === start.col)
        );
        setMergedCells(newMergedCells);
        setSelectionRange(null);
    }, [selectionRange, mergedCells]);

    // Action column renderer
    const renderActionCell = useCallback(({ row }) => {
        if (editingRow === row.id) {
            return (
                <div className="action-buttons-cell">
                    <button onClick={() => saveRowEdit(row)} title="Save" className="action-btn save-btn">
                        <FaSave />
                    </button>
                    <button onClick={cancelRowEdit} title="Cancel" className="action-btn cancel-btn">
                        <FaTimes />
                    </button>
                </div>
            );
        }

        return (
            <div className="action-buttons-cell">
                <button onClick={() => toggleRowEdit(row.id)} title="Edit" className="action-btn edit-btn">
                    <FaEdit />
                </button>
                <button onClick={() => deleteRow(row.id)} title="Delete" className="action-btn delete-btn">
                    <FaTrash />
                </button>
                <button 
                    onClick={() => handleCellSelect(row.id, 'actions')} 
                    title="Merge" 
                    className="action-btn merge-btn"
                    onMouseDown={() => handleCellSelect(row.id, 'actions')}
                    onMouseEnter={() => isSelecting && handleCellSelect(row.id, 'actions')}
                >
                    <FaObjectGroup />
                </button>
            </div>
        );
    }, [editingRow, toggleRowEdit, deleteRow, saveRowEdit, cancelRowEdit, handleCellSelect, isSelecting]);

    // Load sheet data
    const loadSheetData = useCallback((file, sheet) => {
        try {
            const excelFile = excelFiles.find(f => f.name === file);
            if (!excelFile) return;

            const worksheet = excelFile.workbook.Sheets[sheet];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: false });
            
            // Process merged cells
            if (worksheet['!merges']) {
                setMergedCells(worksheet['!merges'].map(merge => ({
                    start: { row: merge.s.r, col: merge.s.c },
                    end: { row: merge.e.r, col: merge.e.c }
                })));
            }

            // Create columns
            const columns = jsonData[0]?.map((col, index) => ({
                key: `col-${index}`,
                name: col?.toString().trim() || String.fromCharCode(65 + index),
                editable: true,
                width: 120,
                resizable: true,
                renderCell: ({ row, onRowChange }) => {
                    const colIdx = index;
                    const isInMerge = mergedCells.some(merge => 
                        row.id >= merge.start.row && 
                        row.id <= merge.end.row && 
                        colIdx >= merge.start.col && 
                        colIdx <= merge.end.col
                    );

                    if (isInMerge) {
                        const merge = mergedCells.find(m => 
                            m.start.row <= row.id && 
                            m.end.row >= row.id && 
                            m.start.col <= colIdx && 
                            m.end.col >= colIdx
                        );

                        // Only render the top-left cell of merged area
                        if (row.id !== merge.start.row || colIdx !== merge.start.col) {
                            return null;
                        }

                        return (
                            <div style={{
                                gridColumn: `span ${merge.end.col - merge.start.col + 1}`,
                                gridRow: `span ${merge.end.row - merge.start.row + 1}`,
                                backgroundColor: '#e6f3ff',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: '100%'
                            }}>
                                {row[`col-${colIdx}`]}
                            </div>
                        );
                    }

                    return (
                        <div 
                            onClick={() => handleCellSelect(row.id, `col-${colIdx}`)}
                            onMouseDown={() => handleCellSelect(row.id, `col-${colIdx}`)}
                            onMouseEnter={() => isSelecting && handleCellSelect(row.id, `col-${colIdx}`)}
                            style={{ 
                                width: '100%', 
                                height: '100%',
                                backgroundColor: selectionRange && 
                                    row.id >= selectionRange.start.row && 
                                    row.id <= selectionRange.end.row && 
                                    colIdx >= selectionRange.start.col && 
                                    colIdx <= selectionRange.end.col 
                                    ? '#d4e6ff' : 'transparent'
                            }}
                        >
                            <input
                                type="text"
                                value={row[`col-${colIdx}`] || ""}
                                onChange={(e) => {
                                    onRowChange({ ...row, [`col-${colIdx}`]: e.target.value });
                                    handleCellEdit(row.id, `col-${colIdx}`, e.target.value);
                                }}
                                style={{ width: '100%', border: 'none', background: 'transparent' }}
                            />
                        </div>
                    );
                }
            })) || [];

            // Add actions column
            const actionColumn = {
                key: 'actions',
                name: 'Actions',
                width: 150,
                frozen: true,
                renderCell: renderActionCell
            };

            const allColumns = [...columns, actionColumn];
    
            const rows = jsonData.slice(1).map((row, rowIndex) => {
                const rowData = { id: rowIndex };
                columns.forEach((col, colIndex) => {
                    rowData[col.key] = row[colIndex] !== undefined ? row[colIndex] : "";
                });
                return rowData;
            });
    
            setGridColumns(allColumns);
            setGridRows(rows);
            setOriginalData({ file, sheet, rows, columns: allColumns });
            setHistory([{ rows, columns: allColumns }]);
            setHistoryIndex(0);
        } catch (error) {
            console.error('Error loading sheet data:', error);
        }
    }, [excelFiles, handleCellSelect, isSelecting, mergedCells, selectionRange, handleCellEdit, renderActionCell]);

    // Download the updated Excel file with headers
    const downloadUpdatedExcel = useCallback(() => {
        if (!selectedFile || !selectedSheet) return;

        // Prepare data with headers
        const headerRow = {};
        gridColumns.forEach(col => {
            if (col.key !== 'actions') { // Exclude actions column from export
                headerRow[col.key] = col.name;
            }
        });

        const dataWithHeaders = [
            headerRow,
            ...gridRows.map(row => {
                const rowData = {};
                gridColumns.forEach(col => {
                    if (col.key !== 'actions') { // Exclude actions column from export
                        rowData[col.key] = row[col.key];
                    }
                });
                return rowData;
            })
        ];

        // Create worksheet
        const worksheet = XLSX.utils.json_to_sheet(dataWithHeaders, { skipHeader: true });

        // Add merged cells (adjusting for header row)
        if (mergedCells.length > 0) {
            worksheet['!merges'] = mergedCells.map(merge => ({
                s: { r: merge.start.row + 1, c: merge.start.col }, // +1 to account for header row
                e: { r: merge.end.row + 1, c: merge.end.col }
            }));
        }

        // Create workbook
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, selectedSheet);

        // Set column widths
        const wscols = gridColumns
            .filter(col => col.key !== 'actions') // Exclude actions column
            .map(col => ({ width: col.width / 8 || 15 }));
        worksheet['!cols'] = wscols;

        // Download
        XLSX.writeFile(workbook, `${selectedFile.split('/').pop().replace('.xlsx', '')}-updated.xlsx`);
    }, [selectedFile, selectedSheet, gridRows, gridColumns, mergedCells]);

    // Download and load Excel files
    const downloadAndLoadExcels = useCallback(async (excelPaths, filesToDownload) => {
        const newExcelFiles = [...excelFiles];
        const newSheetNames = { ...sheetNames };
    
        for (const filePath of filesToDownload) {
            try {
                if (!filePath) continue;
    
                const cleanFileName = filePath.split('/').pop();
                if (!cleanFileName.endsWith('.xlsx') && !cleanFileName.endsWith('.xls')) continue;
                
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
    }, [excelFiles, sheetNames, selectedFile, loadSheetData]);
    
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
    
    const handleFileSelection = (fileName) => {
        setSelectedFile(fileName);
        if (sheetNames[fileName]?.length > 0) {
            setSelectedSheet(sheetNames[fileName][0]);
            loadSheetData(fileName, sheetNames[fileName][0]);
        }
    };

    const handleSheetSelection = (sheetName) => {
        setSelectedSheet(sheetName);
        loadSheetData(selectedFile, sheetName);
    };

    const handleGridChange = (updatedRows) => {
        if (!updatedRows || updatedRows.length === 0) return;
        if (JSON.stringify(updatedRows) === JSON.stringify(gridRows)) return;
    
        setGridRows(updatedRows);
        updateHistory(updatedRows, gridColumns);
    };
    
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
        updateHistory(newRows, newColumns);
    };

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

    const resetFileContent = () => {
        if (originalData.file === selectedFile && originalData.sheet === selectedSheet) {
            setGridRows(originalData.rows);
            setGridColumns(originalData.columns);
            setColumnReduction({});
            setHistory([{ rows: originalData.rows, columns: originalData.columns }]);
            setHistoryIndex(0);
        }
    };

    return (
        <div className="beta-excel-container" onMouseUp={handleMouseUp}>
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

                <label htmlFor="column-select">Select Column:</label>
                <select 
                    id="column-select" 
                    onChange={(e) => setSelectedColumn(e.target.value)} 
                    value={selectedColumn}
                >
                    <option value="">Select Column</option>
                    {gridColumns.filter(col => col.key !== 'actions').map((col) => (
                        <option key={col.key} value={col.key}>{col.name}</option>
                    ))}
                </select>

                <label htmlFor="reduction-factor">Reduction Factor:</label>
                <input 
                    id="reduction-factor"
                    type="number"
                    value={reductionFactor}
                    onChange={(e) => setReductionFactor(Number(e.target.value))}
                    min="1"
                    step="0.1"
                />
                <button 
                    onClick={() => applyColumnReduction(selectedColumn, reductionFactor)} 
                    disabled={!selectedColumn}
                    className="apply-reduction-btn"
                >
                    Apply Reduction
                </button>
            </div>

            {/* Action Buttons */}
            <div className="action-buttons">
                <button onClick={undo} title="Undo"><FaUndo /> Undo</button>
                <button onClick={redo} title="Redo"><FaRedo /> Redo</button>
                <button onClick={resetFileContent} title="Reset"><FaSyncAlt /> Reset</button>
                <button onClick={downloadUpdatedExcel} title="Download Excel"><FaDownload /> Download</button>
                <button onClick={addNewRow} title="Add Row"><FaPlus /> Add Row</button>
                <button onClick={addNewColumn} title="Add Column"><FaPlus /> Add Column</button>
                <button onClick={deleteSelectedColumn} title="Delete Column" disabled={!selectedColumn}>
                    <FaTrash /> Delete Column
                </button>
                <button onClick={handleMergeCells} title="Merge Cells" disabled={!selectionRange}>
                    Merge Cells
                </button>
                <button onClick={handleUnmergeCells} title="Unmerge Cells" disabled={!selectionRange}>
                    Unmerge Cells
                </button>
            </div>

            {/* Data Grid */}
            <div className="excel-table-container">
                {gridRows.length > 0 && gridColumns.length > 0 ? (
                    <div className="table-wrapper">
                        <DataGrid
                            ref={gridRef}
                            columns={gridColumns}
                            rows={gridRows}
                            onRowsChange={handleGridChange}
                            className="react-data-grid excel-table"
                            style={{ minHeight: "400px", width: "100%" }}
                            rowHeight={35}
                            headerRowHeight={40}
                            rowKeyGetter={row => row.id}
                            selectedRows={selectedRows}
                            onSelectedRowsChange={setSelectedRows}
                            renderers={{
                                renderCell: (props) => {
                                    if (props.column.key === 'actions') {
                                        return renderActionCell(props);
                                    }

                                    const colIdx = gridColumns.findIndex(col => col.key === props.column.key);
                                    const isInMerge = mergedCells.some(merge => 
                                        props.row.id >= merge.start.row && 
                                        props.row.id <= merge.end.row && 
                                        colIdx >= merge.start.col && 
                                        colIdx <= merge.end.col
                                    );

                                    if (isInMerge) {
                                        const merge = mergedCells.find(m => 
                                            m.start.row <= props.row.id && 
                                            m.end.row >= props.row.id && 
                                            m.start.col <= colIdx && 
                                            m.end.col >= colIdx
                                        );

                                        // Only render the top-left cell of merged area
                                        if (props.row.id !== merge.start.row || colIdx !== merge.start.col) {
                                            return null;
                                        }

                                        return (
                                            <div style={{
                                                gridColumn: `span ${merge.end.col - merge.start.col + 1}`,
                                                gridRow: `span ${merge.end.row - merge.start.row + 1}`,
                                                backgroundColor: '#e6f3ff',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                height: '100%'
                                            }}>
                                                {props.row[props.column.key]}
                                            </div>
                                        );
                                    }

                                    const isSelected = selectionRange && 
                                        props.row.id >= selectionRange.start.row && 
                                        props.row.id <= selectionRange.end.row && 
                                        colIdx >= selectionRange.start.col && 
                                        colIdx <= selectionRange.end.col;

                                    return (
                                        <div 
                                            onClick={() => handleCellSelect(props.row.id, props.column.key)}
                                            onMouseDown={() => handleCellSelect(props.row.id, props.column.key)}
                                            onMouseEnter={() => isSelecting && handleCellSelect(props.row.id, props.column.key)}
                                            style={{ 
                                                width: '100%', 
                                                height: '100%',
                                                backgroundColor: isSelected ? '#d4e6ff' : 'transparent'
                                            }}
                                        >
                                            <input
                                                type="text"
                                                value={props.row[props.column.key] || ""}
                                                onChange={(e) => {
                                                    props.onRowChange({ 
                                                        ...props.row, 
                                                        [props.column.key]: e.target.value 
                                                    });
                                                    handleCellEdit(props.row.id, props.column.key, e.target.value);
                                                }}
                                                style={{ 
                                                    width: '100%', 
                                                    border: 'none', 
                                                    background: 'transparent' 
                                                }}
                                            />
                                        </div>
                                    );
                                }
                            }}
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