import React, { useState } from 'react';
import axios from 'axios';
import {
    Button,
    TextField,
    Snackbar,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Typography,
} from '@mui/material';
import { useHistory } from 'react-router-dom';
import './styles/CreditUpdateComponent.css';

const CreditUpdateComponent = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [userData, setUserData] = useState(null);
    const [creditCount, setCreditCount] = useState('');
    const [message, setMessage] = useState('');
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarType, setSnackbarType] = useState('success');
    const history = useHistory();

    const handleSearch = async () => {
        try {
            const response = await axios.get(`/user/search?query=${searchQuery}`);
            setUserData(response.data);
            setCreditCount(
                parseFloat(response.data.credit_count || 0).toFixed(2) // Parse credit count as decimal
            );
            showMessage('User found successfully', 'success');
        } catch (error) {
            console.error('Error fetching user data:', error);
            showMessage('User not found', 'error');
        }
    };

    const handleUpdateCredit = async () => {
        try {
            await axios.put(`/credit/update`, {
                entityId: userData.id,
                creditCount: parseFloat(creditCount).toFixed(2), // Send decimal value
            });
            showMessage('Credit updated successfully', 'success');
        } catch (error) {
            console.error('Error updating credit:', error);
            showMessage('Failed to update credit', 'error');
        }
    };

    const showMessage = (message, type) => {
        setMessage(message);
        setSnackbarType(type);
        setShowSnackbar(true);
    };

    const handleSnackbarClose = () => {
        setShowSnackbar(false);
    };

    const handleBack = () => {
        history.push('/'); // Navigate back to the PDF extraction page
    };

    return (
        <div className="credit-update-container">
            <h2 className="page-title">Credit Update</h2>
            <div className="search-section">
                <TextField
                    fullWidth
                    label="Search by Username or Email"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    variant="outlined"
                    className="text-field"
                />
                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleSearch}
                    className="primary-button"
                >
                    Search
                </Button>
            </div>
            {userData && (
                <>
                    <TableContainer component={Paper} className="user-table">
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell><strong>Field</strong></TableCell>
                                    <TableCell><strong>Value</strong></TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                <TableRow>
                                    <TableCell>Username</TableCell>
                                    <TableCell>{userData.username}</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>Email</TableCell>
                                    <TableCell>{userData.email}</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>Account Type</TableCell>
                                    <TableCell>
                                        {userData.company_id ? (
                                            <Typography variant="body2" color="textSecondary">
                                                Business Account for <strong>{userData.company || 'Unknown Company'}</strong>
                                            </Typography>
                                        ) : (
                                            <Typography variant="body2" color="textSecondary">
                                                Personal Account
                                            </Typography>
                                        )}
                                    </TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell>Current Credit</TableCell>
                                    <TableCell>
                                        <TextField
                                            fullWidth
                                            value={creditCount}
                                            onChange={(e) =>
                                                setCreditCount(e.target.value.replace(/[^0-9.]/g, '')) // Allow only numbers and decimals
                                            }
                                            type="text"
                                            variant="outlined"
                                            className="text-field"
                                        />
                                    </TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </TableContainer>
                    <Button
                        fullWidth
                        variant="contained"
                        color="secondary"
                        onClick={handleUpdateCredit}
                        className="secondary-button"
                    >
                        Update Credit
                    </Button>
                </>
            )}
            <Button
                fullWidth
                variant="contained"
                onClick={handleBack}
                className="back-button"
            >
                Back to PDF Extraction
            </Button>
            <Snackbar
                open={showSnackbar}
                autoHideDuration={4000}
                onClose={handleSnackbarClose}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert onClose={handleSnackbarClose} severity={snackbarType}>
                    {message}
                </Alert>
            </Snackbar>
        </div>
    );
};

export default CreditUpdateComponent;
