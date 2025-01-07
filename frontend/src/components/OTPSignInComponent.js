import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';
import { useHistory } from 'react-router-dom';
import './styles/OTPSignInComponent.css';

const OTPSignInComponent = ({ onBack, setToken }) => {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [otp, setOTP] = useState('');
    const [isOTPSent, setIsOTPSent] = useState(false);
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState('success');
    const history = useHistory();

    const handleSendOTP = async () => {
        if (!email) {
            showMessage('Please enter your email', 'error');
            return;
        }

        try {
            await axios.post('/auth/send-otp', { email });
            showMessage('OTP sent to your email', 'success');
            setIsOTPSent(true);
        } catch (error) {
            console.error('Error sending OTP:', error);
            showMessage('Failed to send OTP. Please try again.', 'error');
        }
    };

    const handleVerifyOTP = async () => {
        if (!otp) {
            showMessage('Please enter the OTP', 'error');
            return;
        }

        try {
            const response = await axios.post('/auth/verify-otp', { email, otp });
            const { username, access_token, refresh_token, special_admin } = response.data;

            // Save tokens and user details in localStorage
            setToken(access_token);
            localStorage.setItem('jwt_token', access_token);
            localStorage.setItem('refresh_token', refresh_token);
            localStorage.setItem('special_admin', special_admin); // Store as boolean
            localStorage.setItem('email', email);
            localStorage.setItem('username', username);

            showMessage('OTP verified successfully', 'success');
            history.push('/'); // Navigate to home after verification
        } catch (error) {
            console.error('Error verifying OTP:', error);
            showMessage('Invalid or expired OTP. Please try again.', 'error');
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
        <div className="otp-signin-container">
            <h2>Sign in with OTP</h2>
            <Grid container spacing={2}>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={isOTPSent}
                    />
                </Grid>
                {isOTPSent && (
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Enter OTP"
                            value={otp}
                            onChange={(e) => setOTP(e.target.value)}
                        />
                    </Grid>
                )}
                <Grid item xs={12}>
                    {!isOTPSent ? (
                        <Button variant="contained" color="primary" onClick={handleSendOTP}>
                            Send OTP
                        </Button>
                    ) : (
                        <Button variant="contained" color="primary" onClick={handleVerifyOTP}>
                            Verify OTP
                        </Button>
                    )}
                </Grid>
                <Grid item xs={12}>
                    <Button variant="text" color="secondary" onClick={onBack}>
                        Back to Login
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

export default OTPSignInComponent;
