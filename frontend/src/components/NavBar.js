import React, { useState, useEffect, useRef } from 'react';
import { Link, useHistory, useLocation } from 'react-router-dom';
import axios from 'axios';
import './styles/NavBar.css';
import newLogo from './../assets/logo192.png';

const NavBar = ({ token, setToken, userRole, setUserRole }) => {
    const [remainingCredits, setRemainingCredits] = useState(0);
    const [dropdownVisible, setDropdownVisible] = useState(false);
    const location = useLocation();
    const history = useHistory();
    const currentPath = location.pathname;
    const dropdownRef = useRef(null); // Reference for the dropdown
    const username = localStorage.getItem('username');
    const excludedPaths = ['/login', '/register', '/forgot-password'];

    const fetchCredits = async () => {
        try {
            const response = await axios.get('/credit/remaining', {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('jwt_token')}`,
                },
            });
            setRemainingCredits(response.data.remaining_credits || 0.00);
        } catch (error) {
            console.error('Error fetching remaining credits:', error);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('username');
        localStorage.removeItem('special_admin');
        setToken('');
        setUserRole('user'); // Reset user role to default
        axios.defaults.headers.common['Authorization'] = '';
        setDropdownVisible(false); // Close the dropdown
        history.push('/login');
    };

    const navigateToCreditUpdate = () => {
        setDropdownVisible(false); // Close the dropdown
        history.push('/credit-update');
    };

    const navigateToPurchaseCredits = () => {
        setDropdownVisible(false); // Close the dropdown
        history.push('/payment');
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

    // Fetch credits and user role on mount or token change
    useEffect(() => {
        if (token && !excludedPaths.includes(currentPath)) {
            fetchCredits();

            // Update userRole dynamically if localStorage changes
            const specialAdmin = localStorage.getItem('special_admin') === 'true';
            setUserRole(specialAdmin ? 'special_admin' : 'user');

            const interval = setInterval(() => {
                fetchCredits(); // Fetch credits every 1 minute
            }, 60000); // 60 seconds

            return () => clearInterval(interval); // Cleanup on component unmount
        }
    }, [token, currentPath, setUserRole]);

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
                                {/* Show Special admin menu only if userRole is special_admin */}
                                {userRole === 'special_admin' && (
                                    <div
                                        className="dropdown-item"
                                        onClick={navigateToCreditUpdate}
                                    >
                                        Credit Update
                                    </div>
                                )}
                                {/* Purchase Credits menu */}
                                <div
                                    className="dropdown-item"
                                    onClick={navigateToPurchaseCredits}
                                >
                                    Purchase Credits
                                </div>
                                {/* Logout menu */}
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
