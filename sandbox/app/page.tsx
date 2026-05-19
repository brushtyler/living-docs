import React from 'react';

const SandboxPage = () => {
  return (
    <div id="sandbox-container" className="p-8 bg-gray-100">
      <h1 className="text-2xl font-bold text-purple-600">Feature Enhanced Sandbox</h1>
      <p className="mt-4 text-gray-700" data-testid="description">
        This component now supports enhanced documentation features.
      </p>
      <button id="action-button" className="mt-6 px-4 py-2 bg-green-500 text-white rounded">
        Click Me
      </button>
    </div>
  );
};

export default SandboxPage;
