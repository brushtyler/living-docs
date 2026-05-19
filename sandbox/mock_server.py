from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body>
            <div id="sandbox-container" class="p-8 bg-gray-100">
                <h1 class="text-2xl font-bold text-purple-600">Feature Enhanced Sandbox</h1>
                <p class="mt-4 text-gray-700" data-testid="description">
                    This component now supports enhanced documentation features.
                </p>
                <button id="action-button" class="mt-6 px-4 py-2 bg-green-500 text-white rounded">
                    Click Me
                </button>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Use port 5050 to avoid common conflicts
    app.run(port=5050)
