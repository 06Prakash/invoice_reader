// src/components/NavBar.js

import React from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './styles/NavBar.css';
import newLogo from './../assets/logo192.png'; 

const NavBar = ({ token, setToken }) => {
    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        setToken('');
        axios.defaults.headers.common['Authorization'] = '';
    };

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <img src={newLogo} alt="NIRA Invoice Reader" className="logo" />
                <h1>NIRA Invoice Reader</h1>
            </div>
            <div>
                {token ? (
                    <button onClick={handleLogout} className="nav-button">Logout</button>
                ) : (
                    <>
                        <Link to="/register" className="nav-button">Register</Link>
                        <Link to="/login" className="nav-button">Login</Link>
                    </>
                )}
            </div>
        </nav>
    );
};

export default NavBar;
