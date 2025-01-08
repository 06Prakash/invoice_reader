import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';
import './styles/ResetPasswordComponent.css';

const ResetPasswordComponent = ({ onBack }) => {
    const [email, setEmail] = useState('');
    const [otp, setOTP] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isOTPSent, setIsOTPSent] = useState(false);
    const [isSendingOTP, setIsSendingOTP] = useState(false); // New state to track OTP request
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState('success');

    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$/;

    const handleSendOTP = async () => {
        if (!email) {
            showMessage('Please enter your email', 'error');
            return;
        }

        setIsSendingOTP(true); // Disable button
        try {
            await axios.post('/auth/send-otp', { email });
            showMessage('OTP sent to your email', 'success');
            setIsOTPSent(true);
        } catch (error) {
            console.error('Error sending OTP:', error);
            showMessage('Failed to send OTP. Please try again.', 'error');
        } finally {
            setIsSendingOTP(false); // Re-enable button
        }
    };

    const handleResetPassword = async () => {
        if (!otp || !newPassword || !confirmPassword) {
            showMessage('Please fill in all fields', 'error');
            return;
        }

        if (newPassword !== confirmPassword) {
            showMessage('Passwords do not match', 'error');
            return;
        }

        if (!passwordRegex.test(newPassword)) {
            showMessage(
                'Password must be at least 8 characters long, include uppercase and lowercase letters, a number, and a special character.',
                'error'
            );
            return;
        }

        try {
            await axios.post('/auth/reset-password', { email, otp, newPassword });
            showMessage('Password updated successfully', 'success');
             // Delay navigation by 2 seconds
            setTimeout(() => {
                onBack(); // Navigate back to login
            }, 2000);
        } catch (error) {
            console.error('Error resetting password:', error);
            showMessage('Failed to reset password. Please try again.', 'error');
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
        <div className="reset-password-container">
            <h2>Reset Password</h2>
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
                    <>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Enter OTP"
                                value={otp}
                                onChange={(e) => setOTP(e.target.value)}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                type="password"
                                label="New Password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                type="password"
                                label="Confirm Password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        </Grid>
                    </>
                )}
                <Grid item xs={12}>
                    {!isOTPSent ? (
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={handleSendOTP}
                            disabled={isSendingOTP} // Disable while OTP is being sent
                        >
                            {isSendingOTP ? 'Sending OTP...' : 'Send OTP'}
                        </Button>
                    ) : (
                        <Button variant="contained" color="primary" onClick={handleResetPassword}>
                            Reset Password
                        </Button>
                    )}
                </Grid>
                <Grid item xs={12}>
                    <Button variant="text" color="secondary" onClick={onBack}>
                        Back to Login
                    </Button>
                </Grid>
            </Grid>

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

export default ResetPasswordComponent;
