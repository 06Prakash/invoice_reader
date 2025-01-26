import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';
import { useHistory } from 'react-router-dom';
import OTPSignInComponent from './OTPSignInComponent';
import ResetPasswordComponent from './ResetPasswordComponent'; // Import Reset Password Component
import './styles/LoginComponent.css';

const LoginComponent = ({ setToken, setUserRole }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isOTPSignIn, setIsOTPSignIn] = useState(false); // Toggle OTP sign-in view
    const [isResetPassword, setIsResetPassword] = useState(false); // Toggle Reset Password view
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState('success');
    const history = useHistory();

    // After successful login
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
            localStorage.setItem('special_admin', special_admin);
            localStorage.setItem('username', username);

            // Update user role state dynamically
            setUserRole(special_admin ? 'special_admin' : 'user');

            showMessage('Login successful', 'success');
            history.push('/');
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
                    onBack={() => setIsOTPSignIn(false)}
                    setToken={setToken}
                />
            ) : isResetPassword ? (
                <ResetPasswordComponent onBack={() => setIsResetPassword(false)} />
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
                        <Button
                            variant="contained"
                            className="login-button"
                            onClick={handleLogin}
                            disableElevation
                            disabled={!username || !password} // Disable if fields are empty
                        >
                            Login
                        </Button>
                        </Grid>
                        <Grid item xs={12}>
                            <Button
                                variant="outlined"
                                className="otp-button"
                                onClick={() => setIsOTPSignIn(true)}
                                color="secondary"
                                disableElevation
                            >
                                Sign in with OTP
                            </Button>
                        </Grid>
                        <Grid item xs={12}>
                            <Button
                                variant="text"
                                color="secondary"
                                onClick={() => setIsResetPassword(true)} // Navigate to Reset Password
                            >
                                Forgot Password?
                            </Button>
                        </Grid>
                    </Grid>
                </>
            )}

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
