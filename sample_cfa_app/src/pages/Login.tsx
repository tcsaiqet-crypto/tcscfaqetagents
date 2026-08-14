import React from 'react';

export const Login = () => {
    return (
        <form data-testid="login-form">
            <h2>CFA Applicant Portal Login</h2>
            <input data-testid="username" type="text" placeholder="Username / Email" />
            <input data-testid="password" type="password" placeholder="Password" />
            <button data-testid="login-btn" type="submit">Log In</button>
            <div data-testid="error-alert" style={{display: 'none'}}>Invalid credentials</div>
        </form>
    );
};
