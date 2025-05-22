import React, { useState } from 'react';
import { FaUndo, FaRedo, FaDownload, FaSyncAlt, FaPlus, FaAlignLeft, FaAlignCenter, FaAlignRight } from "react-icons/fa";
import * as XLSX from 'xlsx';
import './styles/ExcelEditorTools.css';

const ExcelEditTools = ({
    selectedFile,
    selectedSheet,
    gridRows,
    setGridRows,
    gridColumns,
    setGridColumns,
    isLoading,
    setIsLoading,
    alignment,
    setAlignment,
    generateId,
    originalData,
    loadSheetData,
    selectedCell
}) => {
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [columnReduction, setColumnReduction] = useState({});
    const [selectedColumn, setSelectedColumn] = useState("");
    const [reductionFactor, setReductionFactor] = useState(1);
    const [showInsertMenu, setShowInsertMenu] = useState(false);

    // Save history function
    const saveToHistory = () => {
        const currentState = {
            rows: [...gridRows],
            columns: [...gridColumns]
        };
        setHistory(prev => [...prev.slice(0, historyIndex + 1), currentState]);
        setHistoryIndex(prev => prev + 1);
    };

    // Add column at end
    const addNewColumn = async () => {
        try {
            setIsLoading(true);
            const newColumnKey = `col-${Date.now()}`; // Define newColumnKey here
            
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

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to add column');
            }

            const newColumn = {
                key: newColumnKey,
                name: data.column_name,
                editable: true,
                width: 200,
                resizable: true,
                idx: gridColumns.length
            };

            setGridColumns([...gridColumns, newColumn]);
            setGridRows(prevRows => 
                prevRows.map(row => ({
                    ...row,
                    [newColumnKey]: ""
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

    // Insert column at position
    const insertColumnAtPosition = async () => {
        if (!selectedCell) {
            alert('Please select a cell to determine position');
            return;
        }
        try {
            setIsLoading(true);
            const position = selectedCell.columnIdx + 1;
            const newColumnKey = `col-${Date.now()}`; // Define newColumnKey here
            
            const response = await fetch('/excel/insert-column', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    column_name: `Column ${gridColumns.length + 1}`,
                    sheet: selectedSheet,
                    position: position
                })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to insert column');
            }

            const newColumn = {
                key: newColumnKey,
                name: data.column_name,
                editable: true,
                width: 200,
                resizable: true,
                idx: position - 1
            };

            // Insert at specific position
            const newColumns = [...gridColumns];
            newColumns.splice(position - 1, 0, newColumn);
            
            // Update indexes for columns after the inserted one
            newColumns.forEach((col, idx) => {
                col.idx = idx;
            });

            setGridColumns(newColumns);
            setGridRows(prevRows => 
                prevRows.map(row => ({
                    ...row,
                    [newColumnKey]: ""
                }))
            );
            saveToHistory();
        } catch (error) {
            console.error('Error inserting column:', error);
            alert(`Error inserting column: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Add row at end
    const addNewRow = async () => {
        try {
            setIsLoading(true);
            const newRow = { id: generateId() };
            gridColumns.forEach(col => {
                newRow[col.key] = "";
            });

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

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to add row');
            }

            setGridRows([...gridRows, newRow]);
            saveToHistory();
        } catch (error) {
            console.error('Error adding row:', error);
            alert(`Error adding row: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Insert row at position
    const insertRowAtPosition = async () => {
        if (!selectedCell) {
            alert('Please select a cell to determine position');
            return;
        }
        try {
            setIsLoading(true);
            const position = selectedCell.rowIdx + 2; // +2 because Excel is 1-based and we have header row
            
            const response = await fetch('/excel/insert-row', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({
                    filename: selectedFile,
                    sheet: selectedSheet,
                    position: position
                })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to insert row');
            }

            const newRow = { id: generateId() };
            gridColumns.forEach(col => {
                newRow[col.key] = "";
            });

            // Insert at specific position
            const newRows = [...gridRows];
            newRows.splice(selectedCell.rowIdx, 0, newRow);

            setGridRows(newRows);
            saveToHistory();
        } catch (error) {
            console.error('Error inserting row:', error);
            alert(`Error inserting row: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
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

            await loadSheetData(selectedFile, selectedSheet);
        } catch (error) {
            console.error('Error deleting row:', error);
            alert(`Error deleting row: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
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

     return (
        <div className="excel-edit-tools">
            <div className="toolbar">
                {/* Insert Menu */}
                <div className="toolbar-group">
                    <button 
                        className="toolbar-button insert-btn"
                        onClick={() => setShowInsertMenu(!showInsertMenu)}
                        title="Insert Options"
                    >
                        <FaPlus /> Insert
                    </button>
                    
                    {showInsertMenu && (
                        <div className="insert-menu">
                            <button 
                                className="menu-item"
                                onClick={insertColumnAtPosition}
                                disabled={!selectedCell || isLoading}
                            >
                                Insert Column Here
                            </button>
                            <button 
                                className="menu-item"
                                onClick={insertRowAtPosition}
                                disabled={!selectedCell || isLoading}
                            >
                                Insert Row Here
                            </button>
                            <button 
                                className="menu-item"
                                onClick={addNewColumn}
                                disabled={isLoading}
                            >
                                Add Column (End)
                            </button>
                            <button 
                                className="menu-item"
                                onClick={addNewRow}
                                disabled={isLoading}
                            >
                                Add Row (End)
                            </button>
                        </div>
                    )}
                </div>

                {/* Keep all other buttons */}
                <button className="toolbar-button" onClick={undo} title="Undo" disabled={historyIndex <= 0 || isLoading}>
                    <FaUndo />
                </button>
                <button className="toolbar-button" onClick={redo} title="Redo" disabled={historyIndex >= history.length - 1 || isLoading}>
                    <FaRedo />
                </button>
                <button className="toolbar-button" onClick={resetFileContent} title="Reset" disabled={isLoading}>
                    <FaSyncAlt />
                </button>
                <button className="toolbar-button" onClick={downloadUpdatedExcel} title="Download Excel" disabled={gridRows.length === 0 || isLoading}>
                    <FaDownload />
                </button>
                
                <div className="alignment-buttons">
                    <button 
                        className={`toolbar-button ${alignment === 'left' ? 'active' : ''}`} 
                        onClick={handleAlignLeft} 
                        title="Align Left" 
                        disabled={isLoading}
                    >
                        <FaAlignLeft />
                    </button>
                    <button 
                        className={`toolbar-button ${alignment === 'center' ? 'active' : ''}`} 
                        onClick={handleAlignCenter} 
                        title="Align Center" 
                        disabled={isLoading}
                    >
                        <FaAlignCenter />
                    </button>
                    <button 
                        className={`toolbar-button ${alignment === 'right' ? 'active' : ''}`} 
                        onClick={handleAlignRight} 
                        title="Align Right" 
                        disabled={isLoading}
                    >
                        <FaAlignRight />
                    </button>
                </div>
            </div>

            {/* Reduction controls */}
            <div className="reduction-controls">
                <select 
                    onChange={(e) => setSelectedColumn(e.target.value)} 
                    value={selectedColumn}
                    disabled={isLoading}
                >
                    <option value="">Select Column</option>
                    {gridColumns.map((col) => (
                        col.key !== 'actions' && <option key={col.key} value={col.key}>{col.name}</option>
                    ))}
                </select>

                <input 
                    type="number"
                    value={reductionFactor}
                    onChange={(e) => setReductionFactor(Number(e.target.value))}
                    min="1"
                    step="0.1"
                    disabled={isLoading}
                    placeholder="Factor"
                />

                <button 
                    className="apply-reduction-btn"
                    onClick={() => applyColumnReduction(selectedColumn, reductionFactor)} 
                    disabled={!selectedColumn || reductionFactor <= 0 || isLoading}
                >
                    Apply Reduction
                </button>
            </div>
        </div>
    );
};

export default ExcelEditTools;