import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';
import './styles/CompanyRegisterComponent.css';

const CompanyRegisterComponent = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [companyName, setCompanyName] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarType, setSnackbarType] = useState('success');

    const handleAddCompany = async () => {
        if (!companyName) {
            showMessage('Company name is required.', 'error');
            return;
        }

        if (!validateEmail(email)) {
            showMessage('Invalid email format.', 'error');
            return;
        }

        try {
            const payload = { company_name: companyName, username, email, password };
            await axios.post('/admin/add-company', payload);
            showMessage('Company and admin added successfully!', 'success');
        } catch (error) {
            console.error('Error adding company:', error);
            showMessage('Failed to add company. Please try again.', 'error');
        }
    };

    const showMessage = (message, type) => {
        setSnackbarType(type);
        setError(type === 'error' ? message : '');
        setSuccess(type === 'success' ? message : '');
        setShowSnackbar(true);
    };

    const handleSnackbarClose = () => {
        setShowSnackbar(false);
    };

    const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    return (
        <div className="company-register-container">
            <h2>Add Company and Admin</h2>
            <Grid container spacing={2}>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Company Name"
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                    />
                </Grid>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </Grid>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </Grid>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        type="password"
                        label="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </Grid>
                <Grid item xs={12}>
                    <Button variant="contained" color="primary" onClick={handleAddCompany}>
                        Add Company and Admin
                    </Button>
                </Grid>
            </Grid>

            {/* Snackbar for success or error messages */}
            <Snackbar
                open={showSnackbar}
                autoHideDuration={4000}
                onClose={handleSnackbarClose}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert onClose={handleSnackbarClose} severity={snackbarType}>
                    {snackbarType === 'success' ? success : error}
                </Alert>
            </Snackbar>
        </div>
    );
};

export default CompanyRegisterComponent;
