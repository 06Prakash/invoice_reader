import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert, CircularProgress } from '@mui/material';
import { useHistory } from 'react-router-dom';
import './styles/OTPSignInComponent.css';

const OTPSignInComponent = ({ onBack, setToken }) => {
    const [email, setEmail] = useState('');
    const [otp, setOTP] = useState('');
    const [isOTPSent, setIsOTPSent] = useState(false);
    const [isLoading, setIsLoading] = useState(false); // State to manage loading state of Send OTP
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState('success');
    const history = useHistory();

    const handleSendOTP = async () => {
        if (!email) {
            showMessage('Please enter your email', 'error');
            return;
        }

        setIsLoading(true); // Start loading
        try {
            await axios.post('/auth/send-otp', { email });
            showMessage('OTP sent to your email', 'success');
            setIsOTPSent(true);
        } catch (error) {
            console.error('Error sending OTP:', error);
            showMessage('Failed to send OTP. Please try again.', 'error');
        } finally {
            setIsLoading(false); // Stop loading
        }
    };

    // In OTPSignInComponent.js, temporarily modify handleVerifyOTP:
	const handleVerifyOTP = async () => {
	  // TEMPORARY HACK - Auto-login for development
	  const mockData = {
		username: "admin",
		access_token: "temp_dev_token",
		refresh_token: "temp_refresh_token",
		special_admin: true
	  };
	  
	  setToken(mockData.access_token);
	  localStorage.setItem('jwt_token', mockData.access_token);
	  localStorage.setItem('refresh_token', mockData.refresh_token);
	  localStorage.setItem('special_admin', mockData.special_admin);
	  localStorage.setItem('email', "dev@example.com");
	  localStorage.setItem('username', mockData.username);
	  
	  history.push('/');
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
                        disabled={isOTPSent || isLoading}
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
                        <Button
                            className="send-otp-button"
                            onClick={handleSendOTP}
                            disabled={isLoading} // Disable button while loading
                            disableElevation
                            startIcon={isLoading && <CircularProgress size={20} />} // Show loader
                        >
                            {isLoading ? 'Sending...' : 'Send OTP'}
                        </Button>
                    ) : (
                        <Button
                            className="verify-otp-button"
                            onClick={handleVerifyOTP}
                            disableElevation
                        >
                            Verify OTP
                        </Button>
                    )}
                </Grid>
                <Grid item xs={12}>
                    <Button
                        variant="text"
                        className="back-button"
                        onClick={onBack}
                    >
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
