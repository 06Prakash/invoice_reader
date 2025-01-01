import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid, Snackbar, Alert } from '@mui/material';
import { useHistory } from 'react-router-dom'; // Replace useNavigate with useHistory
import './styles/LoginComponent.css';

const LoginComponent = ({ setToken }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showSnackbar, setShowSnackbar] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState('success');
    const history = useHistory(); // Initialize useHistory

    const handleLogin = async () => {
        if (!username || !password) {
            showMessage('Please fill in all fields', 'error');
            return;
        }

        try {
            const response = await axios.post('/user/login', { username, password });
            const token = response.data.access_token;
            const isSpecialAdmin = response.data.special_admin;

            // Save token and special_admin status to localStorage
            setToken(token);
            localStorage.setItem('jwt_token', token);
            localStorage.setItem('special_admin', JSON.stringify(isSpecialAdmin));
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

export default LoginComponent;
