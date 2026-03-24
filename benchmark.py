import sys
import os
import time
import numpy as np
import cv2
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kursorin.config import load_config
from kursorin.core.kursorin_engine import KursorinEngine

def run_benchmark():
    logger.info("Initializing KURSORIN Headless Benchmark...")
    config = load_config()
    
    # Disable actual mouse events during benchmark
    config.click.dwell_click_enabled = False
    config.click.pinch_click_enabled = False
    
    engine = KursorinEngine(config)
    engine.initialize()
    
    # We will simulate processing a frame by injecting a static array directly 
    # if a webcam is not available or to strictly measure processing overhead.
    logger.info("Checking for webcam...")
    webcam_available = False
    try:
        frame = engine._camera.read()
        if frame is not None:
            webcam_available = True
            logger.info("Webcam detected. Using live frames for realistic benchmarking.")
    except Exception:
        pass
        
    if not webcam_available:
        logger.warning("No webcam detected. Using synthetic noise frames (FaceMesh will exit early, latency will be artificially low).")
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        engine._camera = type('MockCamera', (), {'read': lambda: frame.copy(), 'open': lambda: None, 'close': lambda: None, 'width': 640, 'height': 480, 'fps': 30})()

    logger.info("Warming up engine (10 frames)...")
    for _ in range(10):
        engine._process_frame()
        
    logger.info("Starting performance loop (200 frames)...")
    latencies = []
    
    for i in range(200):
        start_t = time.perf_counter()
        engine._process_frame()
        end_t = time.perf_counter()
        
        latency_ms = (end_t - start_t) * 1000
        latencies.append(latency_ms)
        
    engine.stop()
    
    avg_lat = np.mean(latencies)
    p50_lat = np.percentile(latencies, 50)
    p95_lat = np.percentile(latencies, 95)
    p99_lat = np.percentile(latencies, 99)
    max_fps = 1000.0 / avg_lat if avg_lat > 0 else 0
    
    print("\n" + "="*50)
    print("🚀 KURSORIN PERFORMANCE BENCHMARK 🚀")
    print("="*50)
    print(f"Total Frames Processed : {len(latencies)}")
    print(f"Average Latency        : {avg_lat:.2f} ms")
    print(f"Median (P50) Latency   : {p50_lat:.2f} ms")
    print(f"P95 Latency            : {p95_lat:.2f} ms")
    print(f"P99 Latency            : {p99_lat:.2f} ms")
    print("-" * 50)
    print(f"Maximum Potential FPS  : {max_fps:.2f} FPS")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_benchmark()
