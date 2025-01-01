import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';

const CreditUpdateComponent = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [userData, setUserData] = useState(null);
    const [creditCount, setCreditCount] = useState('');
    const [message, setMessage] = useState('');
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarType, setSnackbarType] = useState('success');

    const handleSearch = async () => {
        try {
            const response = await axios.get(`/user/search?query=${searchQuery}`);
            setUserData(response.data);
            setCreditCount(response.data.credit_count); // Display current credit count
        } catch (error) {
            console.error('Error fetching user data:', error);
            showMessage('User not found', 'error');
        }
    };

    const handleUpdateCredit = async () => {
        try {
            // Determine if it's a personal user or a company user based on the presence of company_id
            const isUser = !userData.company_id;

            await axios.put(`/credit/update`, {
                entityId: isUser ? userData.id : userData.company_id, // Send user_id or company_id
                creditCount: parseInt(creditCount, 10),
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

    return (
        <div>
            <h2>Credit Update</h2>
            <Grid container spacing={2}>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Search by Username or Email"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </Grid>
                <Grid item xs={12}>
                    <Button variant="contained" color="primary" onClick={handleSearch}>
                        Search
                    </Button>
                </Grid>
                {userData && (
                    <>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Username"
                                value={userData.username}
                                disabled
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Email"
                                value={userData.email}
                                disabled
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Credit Count"
                                value={creditCount}
                                onChange={(e) => setCreditCount(e.target.value)}
                                type="number"
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <Button variant="contained" color="secondary" onClick={handleUpdateCredit}>
                                Update Credit
                            </Button>
                        </Grid>
                    </>
                )}
            </Grid>

            {/* Snackbar for feedback */}
            <Snackbar
                open={showSnackbar}
                autoHideDuration={4000}
                onClose={handleSnackbarClose}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity={snackbarType}>{message}</Alert>
            </Snackbar>
        </div>
    );
};

export default CreditUpdateComponent;
