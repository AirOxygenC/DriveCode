import asyncio
from typing import Dict, List, Optional, ByteString
import numpy as np

# Configuration constants defining the expected audio format
SAMPLE_RATE = 44100  # Standard audio sample rate
SAMPLE_WIDTH = 2     # 16-bit PCM (2 bytes per sample)
CHUNK_SIZE_SAMPLES = 1024 # Number of samples per processing chunk
CHUNK_SIZE_BYTES = CHUNK_SIZE_SAMPLES * SAMPLE_WIDTH

# Type aliases for clarity
StreamID = str
AudioChunk = bytes

class StreamMerger:
    """
    Manages and merges multiple real-time incoming audio streams (e.g., from users
    in a conference call) into a single, synchronized output stream.

    The merging process relies on NumPy for efficient PCM data mixing (summation
    and normalization).
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        """
        Initializes the StreamMerger.

        Args:
            sample_rate: The expected sample rate (Hz) for all input streams.
        
        Raises:
            ImportError: If the 'numpy' library is not available.
        """
        try:
            # Check for numpy dependency needed for efficient mixing
            _ = np.array([0])
        except NameError:
            raise ImportError("StreamMerger requires the 'numpy' library for efficient audio processing.")

        self.sample_rate = sample_rate
        # Dictionary mapping StreamID to its input queue
        self._input_queues: Dict[StreamID, asyncio.Queue[AudioChunk]] = {}
        # The queue holding the merged, synchronized output stream chunks
        self.output_queue: asyncio.Queue[AudioChunk] = asyncio.Queue()
        self._merging_task: Optional[asyncio.Task] = None
        self._is_running = False

    def start(self) -> None:
        """Starts the asynchronous core merging loop."""
        if self._is_running:
            return

        self._is_running = True
        loop = asyncio.get_event_loop()
        self._merging_task = loop.create_task(self._merge_loop())

    async def stop(self) -> None:
        """Stops the asynchronous merging process and cleans up resources."""
        self._is_running = False
        if self._merging_task:
            self._merging_task.cancel()
            try:
                await self._merging_task
            except asyncio.CancelledError:
                pass
        
        # Clear queues if necessary (optional, depending on downstream cleanup)
        for q in self._input_queues.values():
            while not q.empty():
                await q.get()
                q.task_done()
        
    def register_stream(self, stream_id: StreamID) -> asyncio.Queue[AudioChunk]:
        """
        Registers a new input stream and returns the queue where its raw audio
        data chunks should be placed by the network handler.

        Args:
            stream_id: A unique identifier for the stream (e.g., user session ID).

        Returns:
            The asyncio.Queue associated with the registered stream.
        """
        if stream_id in self._input_queues:
            raise ValueError(f"Stream ID '{stream_id}' already registered.")
        
        new_queue: asyncio.Queue[AudioChunk] = asyncio.Queue()
        self._input_queues[stream_id] = new_queue
        return new_queue

    def deregister_stream(self, stream_id: StreamID) -> None:
        """
        Deregisters an input stream, removing it from the merge cycle.

        Args:
            stream_id: The ID of the stream to deregister.
        
        Raises:
            KeyError: If the stream_id is not registered.
        """
        if stream_id in self._input_queues:
            del self._input_queues[stream_id]
        else:
            raise KeyError(f"Stream ID '{stream_id}' not found.")

    def _mix_audio_chunks(self, chunks: List[AudioChunk], count_expected: int) -> AudioChunk:
        """
        Performs high-quality audio mixing (sample summation and clipping).

        It assumes 16-bit PCM audio (np.int16). Missing streams are treated as silence.

        Args:
            chunks: A list of raw audio byte chunks received in the current cycle.
            count_expected: The total number of streams expected in this cycle.

        Returns:
            A single AudioChunk (bytes) representing the merged output.
        """
        
        # If no streams are actively sending data, return a silence chunk
        if not chunks and count_expected == 0:
            return b'\x00' * CHUNK_SIZE_BYTES

        # Define the target length based on the expected chunk size
        target_length = CHUNK_SIZE_SAMPLES
        
        # Convert all received byte chunks to 16-bit NumPy arrays (samples)
        sample_arrays = [np.frombuffer(c, dtype=np.int16) for c in chunks]

        # 1. Synchronization & Padding: Handle streams that arrived late/early
        # We need a unified array length for summation.
        
        # Initialize the mixed array buffer (using 32-bit to prevent overflow during summation)
        mixed_data = np.zeros(target_length, dtype=np.int32)
        
        num_present_streams = len(sample_arrays)
        
        for samples in sample_arrays:
            # Ensure the sample chunk matches the target processing size
            if len(samples) > target_length:
                samples = samples[:target_length]
            elif len(samples) < target_length:
                # Pad with silence if chunk is too short for synchronization window
                samples = np.pad(samples, (0, target_length - len(samples)), 'constant', constant_values=0)
            
            mixed_data += samples.astype(np.int32)

        # 2. Normalization and Clipping
        # To prevent clipping when multiple loud streams are mixed, normalize by the number of streams.
        # However, a simpler, more common approach for VoIP is robust clipping.
        
        # Clip the resulting 32-bit data back down to the 16-bit PCM range
        np.clip(mixed_data, np.iinfo(np.int16).min, np.iinfo(np.int16).max, out=mixed_data)
        
        # Convert back to 16-bit format and return bytes
        return mixed_data.astype(np.int16).tobytes()

    async def _merge_loop(self):
        """
        The core asynchronous loop that attempts to synchronize and pull a chunk
        from every active stream queue at a fixed interval.
        """
        
        # Calculate the processing interval based on chunk size and sample rate
        CHUNK_PROCESSING_TIMEOUT = CHUNK_SIZE_SAMPLES / self.sample_rate

        while self._is_running:
            active_queues = list(self._input_queues.values())
            num_streams = len(active_queues)
            
            if num_streams == 0:
                await asyncio.sleep(CHUNK_PROCESSING_TIMEOUT / 4)
                continue

            # 1. Start tasks to concurrently read from all active queues
            read_tasks: Dict[asyncio.Queue, asyncio.Task[AudioChunk]] = {
                q: asyncio.create_task(q.get()) 
                for q in active_queues
            }
            
            received_chunks: List[AudioChunk] = []
            
            try:
                # Wait for all tasks to complete, or until the fixed processing timeout
                done, pending = await asyncio.wait(
                    read_tasks.values(),
                    timeout=CHUNK_PROCESSING_TIMEOUT,
                    return_when=asyncio.ALL_COMPLETED
                )
                
                # Process successfully retrieved chunks
                for task in done:
                    if not task.cancelled():
                        try:
                            chunk = task.result()
                            received_chunks.append(chunk)
                            # Signal that the item has been retrieved (important if using JoinableQueue)
                            # (asyncio.Queue does not require explicit task_done)
                        except Exception:
                            # Handle stream closure/error during retrieval
                            pass

                # Cancel pending tasks (those that timed out or were blocked)
                for task in pending:
                    task.cancel()
            
            except asyncio.CancelledError:
                # Loop was cancelled by `self.stop()`
                break
            except Exception as e:
                # General error handling
                print(f"StreamMerger runtime error: {e}")
                await asyncio.sleep(0.1)
                continue
            
            # 2. Mix the data (including padding for streams that didn't arrive)
            merged_chunk = self._mix_audio_chunks(received_chunks, num_streams)
            
            # 3. Push the merged result to the output queue
            await self.output_queue.put(merged_chunk)