import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField, Grid } from '@mui/material';
import './RegisterComponent.css';

const RegisterComponent = ({ setToken }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [company, setCompany] = useState('');

    const handleRegister = async () => {
        try {
            const response = await axios.post('http://localhost:5001/user/register', { username, email, password, company });
            setToken(response.data.access_token);
            alert('Registration successful');
        } catch (error) {
            console.error('Error registering:', error);
        }
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
        </div>
    );
};

export default RegisterComponent;
