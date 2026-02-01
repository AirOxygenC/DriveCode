from flask import session, request
from flask_socketio import emit
from app import socketio
from app.services.elevenlabs_service import ElevenLabsService
from app.services.gemini_service import GeminiService
from app.services.github_service import GitHubService
from app.services.generation_service import GenerationService
from app.services.validation_service import ValidationService
import re
import time

eleven_labs_service = ElevenLabsService()
gemini_service = GeminiService()
generation_service = GenerationService()
validation_service = ValidationService()

# Buffer to store audio chunks for each client
audio_buffers = {}

def emit_with_voice(event_name, data, voice_text=None):
    """
    Helper to emit events with optional voice synthesis.
    If voice_text is provided, generates and sends TTS audio.
    """
    emit(event_name, data)
    if voice_text:
        try:
            audio_data = eleven_labs_service.stream_audio(voice_text)
            if audio_data:
                emit('audio_response', {'audio': audio_data.hex()})
        except Exception as e:
            print(f"TTS generation failed: {e}")

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
            # ElevenLabs Scribe returns an object with 'text' or 'words'
            # Extract the text content
            if hasattr(transcription, 'text'):
                user_text = transcription.text
            elif hasattr(transcription, 'words'):
                # Join all word texts
                user_text = ''.join([w.text for w in transcription.words if hasattr(w, 'text')])
            else:
                user_text = str(transcription)

        # Clear buffer
        audio_buffers[sid] = bytearray()

    if user_text:
        print(f"User said: {user_text}")
        emit('user_message', {'content': user_text})
        
        # Check if this is a merge confirmation response
        pending_pr = session.get('pending_pr')
        if pending_pr:
            user_text_lower = user_text.lower()
            # Check for approval keywords
            approval_keywords = ['yes', 'merge', 'approve', 'go ahead', 'do it', 'sure', 'okay']
            rejection_keywords = ['no', 'don\'t', 'cancel', 'stop', 'wait']
            
            if any(keyword in user_text_lower for keyword in approval_keywords):
                # User approved - trigger merge
                handle_confirm_merge({'approved': True})
                return
            elif any(keyword in user_text_lower for keyword in rejection_keywords):
                # User rejected
                handle_confirm_merge({'approved': False})
                return
        
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
        
        # Handoff to Gemini for full agentic workflow
        try:
            # Step 1: Analyze Intent
            emit_with_voice('status_change', {'state': 'ANALYZING', 'description': 'Analyzing your request...'}, 'Analyzing your request')
            intent = gemini_service.analyze_intent(user_text, repo_context=repo_context)
            emit_with_voice('status_change', {'state': 'ANALYZING', 'description': f"Intent: {intent}"}, f"I understand. {intent}")
            print(f"Intent: {intent}")
            
            # Step 2: Determine file path
            emit_with_voice('status_change', {'state': 'GENERATING', 'description': 'Determining file structure...'}, 'Determining where to place the code')
            file_path = generation_service.determine_file_path(intent, repo_context)
            print(f"Target file: {file_path}")
            
            # Step 3: Generate code
            file_name = file_path.split("/")[-1] if file_path else "generated_file"
            emit_with_voice('status_change', {'state': 'GENERATING', 'description': f'Generating code for {file_path}...'}, f'Writing code for {file_name}')
            code = generation_service.generate_code(intent, repo_context, file_path)
            if not code:
                raise Exception("Code generation failed")
            print(f"Generated code ({len(code)} chars)")
            
            # Step 4: Generate tests
            emit_with_voice('status_change', {'state': 'GENERATING', 'description': 'Generating tests...'}, 'Writing tests to ensure code quality')
            test_code = generation_service.generate_tests(code, file_path, intent)
            test_file_name = file_path.split('/')[-1] if file_path else "generated.py"
            test_file_path = f"tests/test_{test_file_name}"
            print(f"Generated tests ({len(test_code)} chars)")
            
            # Step 5: Create PR
            emit_with_voice('status_change', {'state': 'MERGING', 'description': 'Creating pull request...'}, 'Creating pull request on GitHub')
            branch_name = f"drivecode-{int(time.time())}"
            changes = {
                file_path: code,
                test_file_path: test_code
            }
            
            gh = GitHubService(token)
            pr_url = gh.create_pr(
                repo_name=current_repo,
                title=f"DriveCode: {intent}",
                body=f"**Generated by DriveCode**\n\nIntent: {intent}\n\nFiles modified:\n- {file_path}\n- {test_file_path}",
                branch_name=branch_name,
                changes=changes
            )
            
            print(f"PR created: {pr_url}")
            emit_with_voice('status_change', {'state': 'IDLE', 'description': 'Pull request created!'}, 'Pull request created successfully!')
            
            # Store PR info in session for potential merge
            session['pending_pr'] = {
                'repo': current_repo,
                'pr_number': int(pr_url.split('/')[-1]),
                'url': pr_url,
                'branch': branch_name
            }
            
            # Generate voice response
            tts_text = "Pull request created successfully! Do you think it's safe to merge to main?"
            audio_data = eleven_labs_service.stream_audio(tts_text)
            if audio_data:
                emit('audio_response', {'audio': audio_data.hex()})  # Send as hex string
            
            # Ask user for merge confirmation
            emit('merge_confirmation_request', {
                'pr_url': pr_url,
                'message': f"Pull request created successfully! Do you think it's safe to merge to main?"
            })
            emit('user_message', {'content': f"Pull request created: {pr_url}\n\n🤔 Should I merge this to main?"})



        except Exception as e:
            print(f"Error during agentic workflow: {e}")
            emit('status_change', {'state': 'IDLE', 'description': f"Error: {str(e)}"})
            emit('error', {'message': f"Workflow failed: {str(e)}"})
    else:
        emit('error', {'message': 'No speech detected'})

@socketio.on('confirm_merge')
def handle_confirm_merge(data):
    """
    Handle user confirmation to merge PR.
    """
    approved = data.get('approved', False)
    pending_pr = session.get('pending_pr')
    
    if not pending_pr:
        emit('error', {'message': 'No pending PR to merge'})
        return
    
    if not approved:
        emit('status_change', {'state': 'IDLE', 'description': 'Merge cancelled by user'})
        emit('user_message', {'content': '❌ Merge cancelled. PR remains open for manual review.'})
        session.pop('pending_pr', None)
        return
    
    # User approved - merge the PR
    try:
        emit('status_change', {'state': 'MERGING', 'description': 'Merging to main...'})
        token = session.get('github_token')
        gh = GitHubService(token)
        
        success, message = gh.merge_pull_request(
            pending_pr['repo'],
            pending_pr['pr_number'],
            commit_message=f"Auto-merge by DriveCode (user approved)"
        )
        
        if success:
            emit('status_change', {'state': 'IDLE', 'description': 'Successfully merged to main!'})
            success_text = "Successfully merged to main! Your code is now live."
            audio_data = eleven_labs_service.stream_audio(success_text)
            if audio_data:
                emit('audio_response', {'audio': audio_data.hex()})
            emit('user_message', {'content': f"✅ {message}\n\nYour code is now live on main! 🚀"})
        else:
            emit('status_change', {'state': 'IDLE', 'description': 'Merge failed'})
            fail_text = f"Merge failed. {message}"
            audio_data = eleven_labs_service.stream_audio(fail_text)
            if audio_data:
                emit('audio_response', {'audio': audio_data.hex()})
            emit('user_message', {'content': f"❌ {message}"})
        
        session.pop('pending_pr', None)
        
    except Exception as e:
        print(f"Error merging PR: {e}")
        emit('status_change', {'state': 'IDLE', 'description': f'Merge error: {str(e)}'})
        emit('error', {'message': f'Failed to merge: {str(e)}'})

