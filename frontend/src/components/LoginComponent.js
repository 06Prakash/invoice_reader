// src/components/LoginComponent.js

import React, { useState } from 'react';
import axios from 'axios';

const LoginComponent = ({ setToken }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async () => {
        try {
            const response = await axios.post('/user/login', { username, password });
            setToken(response.data.access_token);
            alert('Login successful');
        } catch (error) {
            setError('Login failed: ' + (error.response?.data?.message || error.message));
        }
    };

    return (
        <div>
            <h2>Login</h2>
            {error && <p className="error">{error}</p>}
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button onClick={handleLogin}>Login</button>
        </div>
    );
};

export default LoginComponent;
