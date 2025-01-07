import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';
import { useHistory } from 'react-router-dom';
import OTPSignInComponent from './OTPSignInComponent';
import './styles/LoginComponent.css';

const LoginComponent = ({ setToken }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isOTPSignIn, setIsOTPSignIn] = useState(false); // Toggle OTP sign-in view
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState('success');
    const history = useHistory();

    const handleLogin = async () => {
        if (!username || !password) {
            showMessage('Please fill in all fields', 'error');
            return;
        }

        try {
            const response = await axios.post('/user/login', { username, password });
            const { access_token, refresh_token, special_admin } = response.data;

            // Save tokens and user details in localStorage
            setToken(access_token);
            localStorage.setItem('jwt_token', access_token);
            localStorage.setItem('refresh_token', refresh_token);
            localStorage.setItem('special_admin', special_admin); // Store as boolean
            localStorage.setItem('username', username);

            showMessage('Login successful', 'success');
            history.push('/'); // Navigate to home after login
        } catch (error) {
            console.error('Error logging in:', error);
            showMessage('Invalid username or password', 'error');
        }
    };

    const showMessage = (message, severity) => {
        setSnackbarMessage(message);
        setSnackbarSeverity(severity);
        setShowSnackbar(true);
    };

    const handleSnackbarClose = () => {
        setShowSnackbar(false);
    };

    return (
        <div className="login-container">
            {isOTPSignIn ? (
                <OTPSignInComponent
                    onBack={() => setIsOTPSignIn(false)} // Back to regular login
                    setToken={setToken}
                />
            ) : (
                <>
                    <h2>Login</h2>
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
                                type="password"
                                label="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <Button variant="contained" color="primary" onClick={handleLogin}>
                                Login
                            </Button>
                        </Grid>
                        <Grid item xs={12}>
                            <Button
                                variant="outlined"
                                color="secondary"
                                onClick={() => setIsOTPSignIn(true)} // Navigate to OTP sign-in
                            >
                                Sign in with OTP
                            </Button>
                        </Grid>
                    </Grid>
                </>
            )}

            {/* Snackbar for success or error messages */}
            <Snackbar
                open={showSnackbar}
                autoHideDuration={4000}
                onClose={handleSnackbarClose}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert
                    onClose={handleSnackbarClose}
                    severity={snackbarSeverity}
                    sx={{ width: '100%' }}
                >
                    {snackbarMessage}
                </Alert>
            </Snackbar>
        </div>
    );
};

export default LoginComponent;
