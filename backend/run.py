from app import create_app, socketio
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
