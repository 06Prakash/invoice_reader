import React, { useState } from 'react';
import axios from 'axios';
import {Snackbar, Alert } from '@mui/material';

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

    const handleUsernameChange = (value) => {
        setUsername(value.toLowerCase());
    };

    const handleAddCompany = async () => {
        if (!companyName || !username || !email || !password) {
            showMessage('All fields are required.', 'error');
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
            setCompanyName('');
            setUsername('');
            setEmail('');
            setPassword('');
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

        setTimeout(() => setShowSnackbar(false), 4000);
    };

    const handleSnackbarClose = () => {
        setShowSnackbar(false);
    };

    const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    return (
        <div className="company-register-container">
            <h2>Add Company and Admin</h2>
            <form className="company-register-form">
                <div className="form-group">
                    <label htmlFor="companyName">Company Name</label>
                    <input
                        type="text"
                        id="companyName"
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        placeholder="Enter company name"
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => handleUsernameChange(e.target.value)}
                        placeholder="Enter username"
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="email">Email</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Enter email"
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter password"
                    />
                </div>
                <button
                    type="button"
                    className="submit-button"
                    onClick={handleAddCompany}
                    disabled={!companyName || !username || !email || !password}
                >
                    Add Company and Admin
                </button>
            </form>
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
