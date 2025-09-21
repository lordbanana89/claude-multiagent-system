#!/usr/bin/env python3
"""
Simple Health API Endpoint
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("Starting Health API on http://localhost:5001/api/health")
    app.run(host='0.0.0.0', port=5001, debug=True)