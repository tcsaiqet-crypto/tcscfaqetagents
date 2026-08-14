import React from 'react';

export const DocumentUpload = () => {
    return (
        <div data-testid="doc-upload-container">
            <h3>Upload Supporting Documents</h3>
            <input data-testid="doc-upload-input" type="file" accept=".pdf,.png,.jpg" />
            <button data-testid="upload-submit-btn">Upload Proof of Income</button>
        </div>
    );
};
