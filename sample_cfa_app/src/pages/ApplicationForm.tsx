import React from 'react';

export const ApplicationForm = () => {
    return (
        <form data-testid="cfa-application-form">
            <h2>CFA Digital Application Form</h2>
            <input data-testid="applicant-name" type="text" placeholder="Full Legal Name" />
            <input data-testid="annual-income" type="number" placeholder="Annual Income ($)" />
            <select data-testid="employment-status">
                <option value="Employed">Employed Full-Time</option>
                <option value="Self-Employed">Self-Employed</option>
            </select>
            <button data-testid="next-step-btn">Proceed to Document Upload</button>
            <div data-testid="income-validation-error">Annual income must be greater than $0</div>
        </form>
    );
};
