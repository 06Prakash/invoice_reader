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
    const dropdownRef = useRef(null);
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
        setUserRole('user');
        axios.defaults.headers.common['Authorization'] = '';
        setDropdownVisible(false);
        history.push('/login');
    };

    const navigateToCreditUpdate = () => {
        setDropdownVisible(false);
        history.push('/credit-update');
    };

    const navigateToPurchaseCredits = () => {
        setDropdownVisible(false);
        history.push('/payment');
    };

    const navigateToCompanyRegistration = () => {
        setDropdownVisible(false);
        history.push('/company-register');
    };

    const toggleDropdown = () => {
        if (!dropdownVisible) {
            fetchCredits();
        }
        setDropdownVisible(!dropdownVisible);
    };

    const handleClickOutside = (event) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
            setDropdownVisible(false);
        }
    };

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

    useEffect(() => {
        if (token && !excludedPaths.includes(currentPath)) {
            fetchCredits();

            const specialAdmin = localStorage.getItem('special_admin') === 'true';
            setUserRole(specialAdmin ? 'special_admin' : 'user');

            const interval = setInterval(() => {
                fetchCredits();
            }, 60000);

            return () => clearInterval(interval);
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
                                {/* Special admin menu items */}
                                {userRole === 'special_admin' && (
                                    <>
                                        <div
                                            className="dropdown-item"
                                            onClick={navigateToCompanyRegistration}
                                        >
                                            Company Registration
                                        </div>
                                        <div
                                            className="dropdown-item"
                                            onClick={navigateToCreditUpdate}
                                        >
                                            Credit Update
                                        </div>
                                    </>
                                )}
                                {/* Common menu items */}
                                <div
                                    className="dropdown-item"
                                    onClick={navigateToPurchaseCredits}
                                >
                                    Purchase Credits
                                </div>
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
