from flask import session, request
from flask_socketio import emit
from app import socketio
from app.services.elevenlabs_service import ElevenLabsService
from app.services.gemini_service import GeminiService
from app.services.github_service import GitHubService

eleven_labs_service = ElevenLabsService()
gemini_service = GeminiService()

# Buffer to store audio chunks for each client
audio_buffers = {}

@socketio.on('connect')
def handle_connect(auth):
    print('Client connected')
    audio_buffers[request.sid] = bytearray()
    
    token = auth.get('token') if auth else None
    if token:
        session['github_token'] = token
        print("GitHub token received")
    else:
        print("No GitHub token provided in handshake")
        
    emit('status_change', {'state': 'IDLE', 'description': 'Voice Loop Online'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    if request.sid in audio_buffers:
        del audio_buffers[request.sid]

@socketio.on('audio_stream')
def handle_audio_stream(data):
    # Data is expected to be a binary chunk of audio
    sid = request.sid
    if sid in audio_buffers:
        audio_buffers[sid].extend(data)
        print(f"Received audio chunk: {len(data)} bytes")

@socketio.on('end_of_speech')
def handle_end_of_speech(data):
    # User finished talking. Trigger analysis.
    emit('status_change', {'state': 'ANALYZING', 'description': 'Processing voice command...'})
    
    user_text = data.get('text', '')
    
    # Process audio buffer if available
    sid = request.sid
    if sid in audio_buffers and len(audio_buffers[sid]) > 0:
        print(f"Transcribing {len(audio_buffers[sid])} bytes of audio...")
        emit('status_change', {'state': 'ANALYZING', 'description': 'Transcribing audio...'})
        transcription = eleven_labs_service.transcribe_audio(bytes(audio_buffers[sid]))
        if transcription:
            print(f"Transcription: {transcription}")
            # If transcription is an object, extract text (ElevenLabs returns generic response sometimes)
            # Assuming 'transcription' is just the text or we need to access .text
            # Scribe usually returns a transcription object.
            # Let's handle string or object.
            if hasattr(transcription, 'text'):
                user_text = transcription.text
            else:
                 # Check if it's a list or dictionary if dependent on SDK version
                 user_text = str(transcription)

        # Clear buffer
        audio_buffers[sid] = bytearray()

    if user_text:
        print(f"User said: {user_text}")
        emit('user_message', {'content': user_text})
        
        # Get context from GitHub if token exists
        repo_context = None
        current_repo = data.get('repo_name', 'owner/repo') # Client should send repo name
        token = session.get('github_token')
        
        if token:
            try:
                # Initialize fetching service
                emit('status_change', {'state': 'ANALYZING', 'description': 'Fetching repository context...'})
                gh = GitHubService(token)
                # For MVP, just list files to give the LLM an idea of structure
                files = gh.list_files(current_repo) 
                repo_context = f"Repository Structure ({current_repo}):\n" + "\n".join(files)
                print(f"Context fetched successfully for {current_repo}: {len(files)} files found")
            except Exception as e:
                print(f"Error fetching repo context: {e}")
                repo_context = "Error fetching repository context."
        
        # Handoff to Gemini
        try:
            intent = gemini_service.analyze_intent(user_text, repo_context=repo_context)
            emit('status_change', {'state': 'GENERATING', 'description': f"Intent: {intent}"})
            
            # Synthesize response
            audio_stream = eleven_labs_service.stream_audio(f"Plan: {intent}")
            if audio_stream:
                 emit('audio_output', audio_stream)

        except Exception as e:
            print(f"Error during analysis: {e}")
            emit('status_change', {'state': 'IDLE', 'description': f"Error: {str(e)}"})
            emit('error', {'message': f"AI Analysis failed: {str(e)}"})
    else:
        emit('error', {'message': 'No speech detected'})

@socketio.on('confirm_action')
def handle_confirm_action(data):
    # Handle "Yes, deploy it"
    emit('status_change', {'state': 'MERGING', 'description': 'Merging changes to main...'})
