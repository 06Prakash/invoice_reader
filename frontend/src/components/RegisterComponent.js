import React, { useState } from 'react';
import axios from 'axios';

const RegisterComponent = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [company, setCompany] = useState('');

    const handleRegister = async () => {
        try {
            const response = await axios.post('http://localhost:5001/user/register', { username, email, password, company });
            alert(response.data.message);
        } catch (error) {
            console.error('Error registering:', error);
        }
    };

    return (
        <div>
            <h2>Register</h2>
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <input type="text" placeholder="Company" value={company} onChange={(e) => setCompany(e.target.value)} />
            <button onClick={handleRegister}>Register</button>
        </div>
    );
};

export default RegisterComponent;
