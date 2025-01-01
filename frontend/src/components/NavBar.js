import React, { useState, useEffect, useRef } from 'react';
import { Link, useHistory } from 'react-router-dom';
import axios from 'axios';
import './styles/NavBar.css';
import newLogo from './../assets/logo192.png';

const NavBar = ({ token, setToken }) => {
    const [remainingCredits, setRemainingCredits] = useState(0);
    const [dropdownVisible, setDropdownVisible] = useState(false);
    const history = useHistory();
    const dropdownRef = useRef(null); // Reference for the dropdown
    const username = localStorage.getItem('username');
    const isSpecialAdmin = JSON.parse(localStorage.getItem('special_admin'));

    const fetchCredits = async () => {
        try {
            const response = await axios.get('/credit/remaining', {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('jwt_token')}`,
                },
            });
            setRemainingCredits(response.data.remaining_credits || 0);
        } catch (error) {
            console.error('Error fetching remaining credits:', error);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('username');
        localStorage.removeItem('special_admin');
        setToken('');
        axios.defaults.headers.common['Authorization'] = '';
        setDropdownVisible(false); // Close the dropdown
        history.push('/login');
    };

    const navigateToCreditUpdate = () => {
        setDropdownVisible(false); // Close the dropdown
        history.push('/credit-update');
    };

    const toggleDropdown = () => {
        if (!dropdownVisible) {
            fetchCredits(); // Fetch credits only when the dropdown is opened
        }
        setDropdownVisible(!dropdownVisible);
    };

    const handleClickOutside = (event) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
            setDropdownVisible(false); // Close dropdown if clicked outside
        }
    };

    // Add event listener for clicks outside the dropdown
    useEffect(() => {
        if (dropdownVisible) {
            document.addEventListener('click', handleClickOutside);
        } else {
            document.removeEventListener('click', handleClickOutside);
        }
        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [dropdownVisible]);

    // Fetch credits every 5 minutes (300,000 ms)
    useEffect(() => {
        if (token) {
            fetchCredits(); // Fetch credits immediately on login

            const interval = setInterval(() => {
                fetchCredits(); // Fetch credits every 5 minutes
            }, 300000); // 300,000 milliseconds = 5 minutes

            return () => clearInterval(interval); // Clear interval on component unmount
        }
    }, [token]);

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <img src={newLogo} alt="NIRA: Transforming PDFs with Cutting-Edge AI" className="logo" />
                <h1>NIRA: Transforming PDFs with Cutting-Edge AI</h1>
            </div>
            <div className="user-section">
                {token ? (
                    <div className="user-menu" ref={dropdownRef}>
                        <span onClick={toggleDropdown} className="username">
                            {username} ({remainingCredits} Credits)
                        </span>
                        {dropdownVisible && (
                            <div className="dropdown-menu">
                                {isSpecialAdmin && (
                                    <div
                                        className="dropdown-item"
                                        onClick={navigateToCreditUpdate}
                                    >
                                        Credit Update
                                    </div>
                                )}
                                <div className="dropdown-item" onClick={handleLogout}>
                                    Logout
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div>
                        <Link to="/register" className="nav-button">Register</Link>
                        <Link to="/login" className="nav-button">Login</Link>
                    </div>
                )}
            </div>
        </nav>
    );
};

export default NavBar;
