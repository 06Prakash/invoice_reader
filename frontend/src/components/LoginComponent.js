import React, { useState } from 'react';
import axios from 'axios';

const LoginComponent = ({ setToken }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async () => {
        try {
            const response = await axios.post('http://localhost:5001/user/login', { username, password });
            const token = response.data.access_token;
            localStorage.setItem('jwt_token', token);
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            setToken(token);
            alert('Login successful');
        } catch (error) {
            console.error('Error logging in:', error);
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button onClick={handleLogin}>Login</button>
        </div>
    );
};

export default LoginComponent;
