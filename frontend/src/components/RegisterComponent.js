import React, { useState } from 'react';
import axios from 'axios';
import { useHistory } from 'react-router-dom';
import './styles/RegisterComponent.css';

/**
 * RegisterComponent handles user registration and special admin company creation.
 *
 * @param {Function} setToken Callback to store the access token.
 * @param {string} userRole The role of the user (e.g., "special_admin").
 * @return {JSX.Element} The rendered registration form component.
 */
const RegisterComponent = ({ setToken, userRole }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [companyName, setCompanyName] = useState('');
    const [message, setMessage] = useState({ text: '', type: '' });
    const [isSpecialAdmin, setIsSpecialAdmin] = useState(userRole === 'special_admin');
    const [isUsernameValid, setIsUsernameValid] = useState(false);
    const [checkingUsername, setCheckingUsername] = useState(false);

    const history = useHistory();

    /**
     * Checks if the username is available when the user moves focus away from the field.
     *
     * @return {void}
     */
    const checkUsernameAvailability = async () => {
        if (!username.trim()) return;

        setCheckingUsername(true);
        try {
            const response = await axios.get(`/user/checkuser?username=${username.trim().toLowerCase()}`);
            setIsUsernameValid(response.data.available);
            setMessage({ text: response.data.message, type: response.data.available ? 'success' : 'error' });
        } catch (error) {
            console.error('Error checking username:', error);
            setMessage({ text: 'Error checking username', type: 'error' });
        }
        setCheckingUsername(false);
    };

    /**
     * Handles the registration process.
     *
     * Validates the email format and company name (if applicable) before sending a registration
     * request to the server. Displays a success or error message based on the response.
     *
     * @return {void}
     */
    const handleRegister = async () => {
        if (!isUsernameValid) {
            setMessage({ text: 'Please choose a different username', type: 'error' });
            return;
        }

        if (isSpecialAdmin && !companyName) {
            setMessage({ text: 'Company name is required for special admins.', type: 'error' });
            return;
        }

        if (!validateEmail(email)) {
            setMessage({ text: 'Invalid email format', type: 'error' });
            return;
        }

        try {
            const endpoint = isSpecialAdmin ? '/admin/add-company' : '/user/register';
            const payload = isSpecialAdmin
                ? { company_name: companyName, username, email, password }
                : { username, email, password };

            const response = await axios.post(endpoint, payload);

            if (!isSpecialAdmin) {
                setToken(response.data.access_token);
                setTimeout(() => history.push('/login'), 2000);
            }
            setMessage({ text: 'Registration successful', type: 'success' });
        } catch (error) {
            console.error('Error registering:', error);
            setMessage({ text: 'Registration failed. Please try again.', type: 'error' });
        }
    };

    /**
     * Validates the provided email address using a regular expression.
     *
     * @param {string} email The email address to validate.
     * @return {boolean} Returns true if the email format is valid, otherwise false.
     */
    const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    return (
        <div className="register-container">
            <h2>{isSpecialAdmin ? 'Add Company and Admin' : 'Register'}</h2>

            {message.text && (
                <div className={`message-box ${message.type === 'error' ? 'error' : 'success'}`}>
                    {message.text}
                </div>
            )}

            <form onSubmit={(e) => e.preventDefault()}>
                {isSpecialAdmin && (
                    <div className="form-group">
                        <label>Company Name</label>
                        <input
                            type="text"
                            value={companyName}
                            onChange={(e) => setCompanyName(e.target.value)}
                            required
                        />
                    </div>
                )}
                <div className="form-group">
                    <label>Username</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value.toLowerCase())}
                        onBlur={checkUsernameAvailability} // Checks availability on losing focus
                        required
                    />
                    {checkingUsername && <span className="checking-text">Checking...</span>}
                </div>
                <div className="form-group">
                    <label>Email</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label>Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button
                    type="button"
                    className="register-button"
                    onClick={handleRegister}
                    disabled={!isUsernameValid || checkingUsername} // Disabled if username is taken
                >
                    {isSpecialAdmin ? 'Add Company and Admin' : 'Register'}
                </button>
            </form>

            {!isSpecialAdmin && (
                <p className="helpdesk-info">
                    For enterprise or organizational accounts, please contact our helpdesk at{' '}
                    <a href="mailto:helpdesk@niraitsolutions.com">helpdesk@niraitsolutions.com</a>.
                </p>
            )}
        </div>
    );
};

export default RegisterComponent;
