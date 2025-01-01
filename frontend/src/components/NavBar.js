import React, { useState } from 'react';
import { Link, useHistory } from 'react-router-dom'; // Replace useNavigate with useHistory
import axios from 'axios';
import './styles/NavBar.css';
import newLogo from './../assets/logo192.png'; 

const NavBar = ({ token, setToken }) => {
    const [remainingCredits, setRemainingCredits] = useState(0);
    const [dropdownVisible, setDropdownVisible] = useState(false);
    const history = useHistory(); // Use useHistory instead of useNavigate
    const username = localStorage.getItem('username');
    const isSpecialAdmin = JSON.parse(localStorage.getItem('special_admin'));

    const fetchCredits = async () => {
        try {
            const response = await axios.get('/credit/remaining', {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('jwt_token')}`
                }
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
        history.push('/login'); // Use history.push instead of navigate
    };

    const toggleDropdown = () => {
        if (!dropdownVisible) {
            fetchCredits(); // Fetch credits only when the dropdown is opened
        }
        setDropdownVisible(!dropdownVisible);
    };

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <img src={newLogo} alt="NIRA: Transforming PDFs with Cutting-Edge AI" className="logo" />
                <h1>NIRA: Transforming PDFs with Cutting-Edge AI</h1>
            </div>
            <div className="user-section">
                {token ? (
                    <div className="user-menu">
                        <span onClick={toggleDropdown} className="username">
                            {username} ({remainingCredits} Credits)
                        </span>
                        {dropdownVisible && (
                            <div className="dropdown-menu">
                                {isSpecialAdmin && (
                                    <div
                                        className="dropdown-item"
                                        onClick={(event) => {
                                            // event.stopPropagation(); // Prevent event bubbling
                                            console.log('Navigating to /credit-update');
                                            history.push('/credit-update'); // Navigate to Credit Update page
                                        }}
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
