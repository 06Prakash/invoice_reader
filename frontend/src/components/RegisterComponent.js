import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert, Typography } from '@mui/material';
import { useHistory } from 'react-router-dom';
import './styles/RegisterComponent.css';

const RegisterComponent = ({ setToken, userRole }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [companyName, setCompanyName] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isSpecialAdmin, setIsSpecialAdmin] = useState(userRole === 'special_admin');
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarType, setSnackbarType] = useState('success');

    const history = useHistory();

    const handleUsernameChange = (value) => {
        setUsername(value.toLowerCase());
    };

    const handleRegister = async () => {
        if (isSpecialAdmin && !companyName) {
            showMessage('Company name is required for special admins.', 'error');
            return;
        }

        if (!validateEmail(email)) {
            showMessage('Invalid email format', 'error');
            return;
        }

        try {
            const endpoint = isSpecialAdmin ? '/admin/add-company' : '/user/register';
            const payload = isSpecialAdmin
                ? { company_name: companyName, username, email, password }
                : { username, email, password };

            const response = await axios.post(endpoint, payload);

            if (!isSpecialAdmin) {
                setToken(response.data.access_token);
                setTimeout(() => history.push('/login'), 2000);
            }
            showMessage('Registration successful', 'success');
        } catch (error) {
            console.error('Error registering:', error);
            showMessage('Registration failed. Please try again.', 'error');
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
        <div className="register-container">
            <h2>{isSpecialAdmin ? 'Add Company and Admin' : 'Register'}</h2>
            <Grid container spacing={2}>
                {isSpecialAdmin && (
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Company Name"
                            value={companyName}
                            onChange={(e) => setCompanyName(e.target.value)}
                        />
                    </Grid>
                )}
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Username"
                        value={username}
                        onChange={(e) => handleUsernameChange(e.target.value)}
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
                    <Button variant="contained" color="primary" onClick={handleRegister}>
                        {isSpecialAdmin ? 'Add Company and Admin' : 'Register'}
                    </Button>
                </Grid>
            </Grid>
            {/* Information message for enterprise users */}
            {!isSpecialAdmin && (
                <div style={{ marginTop: '20px', textAlign: 'center' }}>
                    <Typography variant="body2" color="textSecondary">
                        For enterprise or organizational accounts, please contact our helpdesk at{' '}
                        <a href="mailto:helpdesk@niraitsolutions.com" style={{ color: '#1976d2' }}>
                            helpdesk@niraitsolutions.com
                        </a>.
                    </Typography>
                </div>
            )}

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

export default RegisterComponent;
