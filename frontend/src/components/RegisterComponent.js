import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';
import { useHistory } from 'react-router-dom'; // Use `useHistory` for navigation
import './styles/RegisterComponent.css';

const RegisterComponent = ({ setToken }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [company, setCompany] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarType, setSnackbarType] = useState('success'); // 'success' or 'error'

    const history = useHistory(); // Initialize `useHistory` for navigation

    const handleRegister = async () => {
        if (!validateEmail(email)) {
            showMessage('Invalid email format', 'error');
            return;
        }

        try {
            const response = await axios.post('/user/register', {
                username,
                email,
                password,
                company,
            });
            setToken(response.data.access_token);
            showMessage('Registration successful', 'success');
            setTimeout(() => history.push('/login'), 2000); // Redirect to login after 2 seconds
        } catch (error) {
            console.error('Error registering:', error);
            showMessage('Registration failed. Please try again.', 'error');
        }
    };

    const validateEmail = (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
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

    return (
        <div className="register-container">
            <h2>Register</h2>
            <Grid container spacing={2}>
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
                        error={!!error && error.includes('email')}
                        helperText={error.includes('email') ? error : ''}
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
                    <TextField
                        fullWidth
                        label="Company"
                        value={company}
                        onChange={(e) => setCompany(e.target.value)}
                    />
                </Grid>
                <Grid item xs={12}>
                    <Button variant="contained" color="primary" onClick={handleRegister}>
                        Register
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
                <Alert onClose={handleSnackbarClose} severity={snackbarType} sx={{ width: '100%' }}>
                    {snackbarType === 'success' ? success : error}
                </Alert>
            </Snackbar>
        </div>
    );
};

export default RegisterComponent;
