from app import create_app
from flask_cors import CORS

app = create_app()  # create Flask app from __init__.py
CORS(app, origins=["http://localhost:5173"])
if __name__ == "__main__":
    # Runs the app in development mode
    app.run(debug=True, host="0.0.0.0", port=5000)