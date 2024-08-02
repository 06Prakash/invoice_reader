// src/components/RegisterComponent.js

import React, { useState } from 'react';
import axios from 'axios';

const RegisterComponent = ({ setToken }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [company, setCompany] = useState('');
    const [error, setError] = useState('');

    const handleRegister = async () => {
        try {
            const response = await axios.post('/user/register', { username, email, password, company });
            setToken(response.data.access_token);
            alert('Registration successful');
        } catch (error) {
            setError('Registration failed: ' + (error.response?.data?.message || error.message));
        }
    };

    return (
        <div>
            <h2>Register</h2>
            {error && <p className="error">{error}</p>}
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <input type="text" placeholder="Company" value={company} onChange={(e) => setCompany(e.target.value)} />
            <button onClick={handleRegister}>Register</button>
        </div>
    );
};

export default RegisterComponent;
