import pytest
import asyncio
import numpy as np
from typing import List, Dict

# Assuming the constants and the StreamMerger class are available from the source file
# For testing purposes, we redefine constants to ensure local availability for helper functions.
SAMPLE_RATE = 44100
SAMPLE_WIDTH = 2
CHUNK_SIZE_SAMPLES = 1024
CHUNK_SIZE_BYTES = CHUNK_SIZE_SAMPLES * SAMPLE_WIDTH

# Helper function to create mock audio chunks
def create_mock_chunk(value: int, num_samples: int = CHUNK_SIZE_SAMPLES) -> bytes:
    """Creates a 16-bit PCM chunk where every sample is 'value'."""
    arr = np.full(num_samples, value, dtype=np.int16)
    return arr.tobytes()

# Helper function to convert bytes back to samples for verification
def bytes_to_samples(chunk: bytes) -> np.ndarray:
    return np.frombuffer(chunk, dtype=np.int16)

# --- Fixtures ---

@pytest.fixture(scope="module")
def StreamMerger():
    # Dynamically import the class assuming it's in the current context/module
    from stream_merger import StreamMerger as SM
    return SM

@pytest.fixture
def stream_merger(StreamMerger):
    merger = StreamMerger(sample_rate=SAMPLE_RATE)
    return merger

@pytest.fixture
def audio_chunk_silence():
    return b'\x00' * CHUNK_SIZE_BYTES

@pytest.fixture
def audio_chunk_medium():
    # Value that is safe for summing two streams (16000 * 2 = 32000)
    return create_mock_chunk(16000)

@pytest.fixture
def audio_chunk_max_clip():
    # Value guaranteed to cause clipping if added to itself (30000 * 2 = 60000)
    return create_mock_chunk(30000)

# --- Initialization and State Tests ---

@pytest.mark.asyncio
async def test_merger_initialization_state(stream_merger):
    assert stream_merger.sample_rate == SAMPLE_RATE
    assert stream_merger._is_running is False
    assert isinstance(stream_merger._input_queues, dict)
    assert isinstance(stream_merger.output_queue, asyncio.Queue)

# --- Stream Management Tests ---

@pytest.mark.asyncio
async def test_register_and_deregister_stream_happy_path(stream_merger):
    stream_id_1 = "user_A"
    stream_id_2 = "user_B"

    q1 = stream_merger.register_stream(stream_id_1)
    q2 = stream_merger.register_stream(stream_id_2)

    assert stream_id_1 in stream_merger._input_queues
    assert len(stream_merger._input_queues) == 2

    stream_merger.deregister_stream(stream_id_1)
    assert stream_id_1 not in stream_merger._input_queues
    assert len(stream_merger._input_queues) == 1

@pytest.mark.asyncio
async def test_register_duplicate_stream_raises_error(stream_merger):
    stream_id = "user_dup"
    stream_merger.register_stream(stream_id)
    with pytest.raises(ValueError, match="already registered"):
        stream_merger.register_stream(stream_id)

@pytest.mark.asyncio
async def test_deregister_nonexistent_stream_raises_error(stream_merger):
    with pytest.raises(KeyError, match="not found"):
        stream_merger.deregister_stream("nonexistent_id")

# --- Mixing Logic Tests (`_mix_audio_chunks`) ---

def test_mix_audio_chunks_returns_silence_when_no_input(stream_merger):
    # Test case: 0 streams registered, 0 chunks received
    result = stream_merger._mix_audio_chunks(chunks=[], count_expected=0)
    assert len(result) == CHUNK_SIZE_BYTES
    assert bytes_to_samples(result).sum() == 0

def test_mix_audio_chunks_returns_silence_when_streams_registered_but_no_chunks(stream_merger):
    # Test case: N streams registered, 0 chunks received (this represents N missing packets)
    result = stream_merger._mix_audio_chunks(chunks=[], count_expected=5)
    assert len(result) == CHUNK_SIZE_BYTES
    assert bytes_to_samples(result).sum() == 0

def test_mix_audio_chunks_single_stream_passthrough(stream_merger, audio_chunk_medium):
    expected_samples = bytes_to_samples(audio_chunk_medium)
    result = stream_merger._mix_audio_chunks(chunks=[audio_chunk_medium], count_expected=1)
    assert np.array_equal(bytes_to_samples(result), expected_samples)

def test_mix_audio_chunks_summation_without_clipping(stream_merger, audio_chunk_medium):
    # Sum two 16000 streams -> Result should be 32000
    chunk1 = audio_chunk_medium
    chunk2 = audio_chunk_medium
    
    result = stream_merger._mix_audio_chunks(chunks=[chunk1, chunk2], count_expected=2)
    result_samples = bytes_to_samples(result)
    
    assert np.all(result_samples == 32000)

def test_mix_audio_chunks_clipping_at_max_value(stream_merger, audio_chunk_max_clip):
    # Sum two 30000 streams (Total 60000) -> Should clip at INT16_MAX (32767)
    MAX_16BIT = np.iinfo(np.int16).max 
    
    result = stream_merger._mix_audio_chunks(chunks=[audio_chunk_max_clip, audio_chunk_max_clip], count_expected=2)
    result_samples = bytes_to_samples(result)
    
    assert np.all(result_samples == MAX_16BIT)

def test_mix_audio_chunks_padding_for_short_chunk(stream_merger):
    # Chunk half the size (512 samples)
    short_chunk = create_mock_chunk(100, num_samples=CHUNK_SIZE_SAMPLES // 2)
    
    result = stream_merger._mix_audio_chunks(chunks=[short_chunk], count_expected=1)
    result_samples = bytes_to_samples(result)
    
    # First half should be data, second half should be padded silence (0)
    assert len(result_samples) == CHUNK_SIZE_SAMPLES
    assert np.all(result_samples[:512] == 100)
    assert np.all(result_samples[512:] == 0)

def test_mix_audio_chunks_truncation_for_long_chunk(stream_merger):
    # Chunk 50% longer (1536 samples)
    long_chunk = create_mock_chunk(500, num_samples=CHUNK_SIZE_SAMPLES + CHUNK_SIZE_SAMPLES // 2)

    result = stream_merger._mix_audio_chunks(chunks=[long_chunk], count_expected=1)
    result_samples = bytes_to_samples(result)

    # Should be truncated back to 1024 samples
    assert len(result_samples) == CHUNK_SIZE_SAMPLES
    assert np.all(result_samples == 500)

# --- Asynchronous Lifecycle Tests ---

@pytest.mark.asyncio
async def test_start_stop_merging_lifecycle(stream_merger):
    stream_merger.start()
    await asyncio.sleep(0.01) # Give time for the task to be scheduled

    assert stream_merger._is_running
    assert stream_merger._merging_task is not None
    
    await stream_merger.stop()

    # The task should be marked as done (cancelled)
    await asyncio.sleep(0.01) 
    assert not stream_merger._is_running
    assert stream_merger._merging_task.done()

@pytest.mark.asyncio
async def test_stop_drains_input_queues(stream_merger, audio_chunk_medium):
    q_a = stream_merger.register_stream("user_A")
    q_b = stream_merger.register_stream("user_B")

    await q_a.put(audio_chunk_medium)
    await q_a.put(audio_chunk_medium)
    await q_b.put(audio_chunk_medium)
    
    stream_merger.start()
    await asyncio.sleep(0.001) # Start loop initialization
    
    assert q_a.qsize() == 2
    
    await stream_merger.stop()
    
    # Input queues should be empty after stop cleanup
    assert q_a.empty()
    assert q_b.empty()

@pytest.mark.asyncio
async def test_merge_loop_synchronous_mixing(stream_merger, audio_chunk_medium):
    q_a = stream_merger.register_stream("A")
    q_b = stream_merger.register_stream("B")
    
    CHUNK_PROCESSING_TIMEOUT = CHUNK_SIZE_SAMPLES / SAMPLE_RATE
    
    stream_merger.start()

    # Cycle 1: Both streams send data
    await q_a.put(audio_chunk_medium)
    await q_b.put(audio_chunk_medium)

    # Wait for the first processing cycle
    await asyncio.sleep(CHUNK_PROCESSING_TIMEOUT * 1.5) 

    assert stream_merger.output_queue.qsize() == 1
    
    # Verify the chunk is summed (32000)
    out_chunk = await stream_merger.output_queue.get()
    assert np.all(bytes_to_samples(out_chunk) == 32000)
    
    await stream_merger.stop()

@pytest.mark.asyncio
async def test_merge_loop_timeout_results_in_silence_padding(stream_merger, audio_chunk_medium):
    q_fast = stream_merger.register_stream("Fast")
    q_slow = stream_merger.register_stream("Slow")
    
    CHUNK_PROCESSING_TIMEOUT = CHUNK_SIZE_SAMPLES / SAMPLE_RATE

    stream_merger.start()
    
    # Cycle 1: Only fast stream sends data immediately
    await q_fast.put(audio_chunk_medium)
    
    # Wait for the timeout (q_slow task should be cancelled/timeout, resulting in silence)
    await asyncio.sleep(CHUNK_PROCESSING_TIMEOUT * 1.1)

    assert stream_merger.output_queue.qsize() == 1
    
    # Result should be 16000 (Fast) + 0 (Slow silence) = 16000
    merged_chunk = await stream_merger.output_queue.get()
    assert np.all(bytes_to_samples(merged_chunk) == 16000)
    
    await stream_merger.stop()

@pytest.mark.asyncio
async def test_merge_loop_handles_zero_active_streams(stream_merger, mocker):
    q_a = stream_merger.register_stream("A")
    sleep_mock = mocker.patch('asyncio.sleep')
    
    stream_merger.start()
    await asyncio.sleep(0.005) # Start loop

    # Deregister the only stream
    stream_merger.deregister_stream("A")
    
    await asyncio.sleep(0.01) # Allow loop to process the next iteration
    
    # The loop should now hit the `num_streams == 0` path and sleep
    sleep_mock.assert_called() 
    
    await stream_merger.stop()

@pytest.mark.asyncio
async def test_cancellation_of_merging_task_during_wait(stream_merger, mocker):
    q_a = stream_merger.register_stream("A")
    
    # Use a large timeout to ensure the task is running when we cancel
    MOCK_TIMEOUT = 10 
    mocker.patch.object(stream_merger, '_merge_loop', wraps=stream_merger._merge_loop)
    mocker.patch('asyncio.wait', autospec=True, side_effect=lambda *args, **kwargs: asyncio.sleep(MOCK_TIMEOUT))
    
    stream_merger.start()
    await asyncio.sleep(0.001) 

    # Verify task is running
    assert stream_merger._is_running

    # Stop the merger, which cancels the task
    await stream_merger.stop()

    # The merge loop should exit cleanly due to CancelledError handling
    assert stream_merger._merging_task.done()