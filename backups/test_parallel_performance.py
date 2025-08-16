#!/usr/bin/env python3
"""
Performance test script for parallel scraping improvements
Tests both traditional batch processing and new parallel optimizations
"""

import requests
import time
import json
import asyncio
import aiohttp
import statistics
from typing import List, Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_DOMAINS = [
    "httpbin.org",
    "example.com", 
    "google.com",
    "github.com",
    "stackoverflow.com",
    "reddit.com",
    "wikipedia.org",
    "youtube.com",
    "amazon.com",
    "microsoft.com",
    "apple.com",
    "netflix.com",
    "linkedin.com",
    "twitter.com",
    "facebook.com",
    "instagram.com",
    "pinterest.com",
    "medium.com",
    "shopify.com",
    "wordpress.com"
]

def test_api_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("+ API is running and healthy")
            return True
        else:
            print(f"- API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"- API is not accessible: {e}")
        print("  Make sure to start the API first:")
        print("  python main.py")
        return False

def test_traditional_batch_processing(domains: List[str], batch_size: int = 10) -> Dict[str, Any]:
    """Test traditional batch processing endpoint"""
    print(f"\n=== Testing Traditional Batch Processing ===")
    print(f"Domains: {len(domains)}, Batch Size: {batch_size}")
    
    payload = {
        "domains": domains,
        "batch_size": batch_size,
        "timeout": 15
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-batch",
            json=payload,
            timeout=300  # 5 minutes
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if response.status_code == 200:
            results = response.json()
            successful_results = len([r for r in results if r.get('status') != 'Error'])
            
            print(f"+ Batch processing completed successfully")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  Successful results: {successful_results}/{len(domains)}")
            print(f"  Average time per domain: {total_time/len(domains):.2f} seconds")
            print(f"  Throughput: {len(domains)/total_time:.2f} domains/second")
            
            return {
                "method": "batch",
                "total_time": total_time,
                "successful_results": successful_results,
                "total_domains": len(domains),
                "avg_time_per_domain": total_time/len(domains),
                "throughput": len(domains)/total_time
            }
        else:
            print(f"- Batch processing failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return {"method": "batch", "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"- Batch processing request failed: {e}")
        return {"method": "batch", "error": str(e)}

def test_parallel_processing(domains: List[str], batch_size: int = 20) -> Dict[str, Any]:
    """Test new parallel processing endpoint"""
    print(f"\n=== Testing Parallel Processing ===")
    print(f"Domains: {len(domains)}, Batch Size: {batch_size}")
    
    payload = {
        "domains": domains,
        "batch_size": batch_size,
        "timeout": 15
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=payload,
            timeout=300  # 5 minutes
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if response.status_code == 200:
            results = response.json()
            successful_results = len([r for r in results if r.get('status') != 'Error'])
            
            print(f"+ Parallel processing completed successfully")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  Successful results: {successful_results}/{len(domains)}")
            print(f"  Average time per domain: {total_time/len(domains):.2f} seconds")
            print(f"  Throughput: {len(domains)/total_time:.2f} domains/second")
            
            return {
                "method": "parallel",
                "total_time": total_time,
                "successful_results": successful_results,
                "total_domains": len(domains),
                "avg_time_per_domain": total_time/len(domains),
                "throughput": len(domains)/total_time
            }
        else:
            print(f"- Parallel processing failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return {"method": "parallel", "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"- Parallel processing request failed: {e}")
        return {"method": "parallel", "error": str(e)}

def test_job_queue_processing(domains: List[str], batch_size: int = 25) -> Dict[str, Any]:
    """Test job queue processing endpoint"""
    print(f"\n=== Testing Job Queue Processing ===")
    print(f"Domains: {len(domains)}, Batch Size: {batch_size}")
    
    payload = {
        "domains": domains,
        "batch_size": batch_size,
        "timeout": 15,
        "priority": 2
    }
    
    start_time = time.time()
    
    try:
        # Submit job
        response = requests.post(
            f"{API_BASE_URL}/jobs/submit",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"- Job submission failed: {response.status_code}")
            return {"method": "job_queue", "error": f"HTTP {response.status_code}"}
        
        job_data = response.json()
        job_id = job_data.get("job_id")
        print(f"+ Job submitted successfully: {job_id}")
        
        # Poll for completion
        completed = False
        max_wait_time = 300  # 5 minutes
        poll_interval = 2  # 2 seconds
        
        while not completed and (time.time() - start_time) < max_wait_time:
            time.sleep(poll_interval)
            
            status_response = requests.get(f"{API_BASE_URL}/jobs/{job_id}/status", timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                job_status = status_data.get("status")
                processed = status_data.get("processed_domains", 0)
                total = status_data.get("total_domains", len(domains))
                
                print(f"  Job status: {job_status}, Progress: {processed}/{total}")
                
                if job_status == "completed":
                    completed = True
                elif job_status == "failed":
                    print(f"- Job failed: {status_data.get('error', 'Unknown error')}")
                    return {"method": "job_queue", "error": "Job failed"}
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if completed:
            # Get results
            results_response = requests.get(f"{API_BASE_URL}/jobs/{job_id}/results", timeout=30)
            if results_response.status_code == 200:
                results_data = results_response.json()
                results = results_data.get("results", [])
                successful_results = len([r for r in results if r.get('status') != 'Error'])
                
                print(f"+ Job queue processing completed successfully")
                print(f"  Total time: {total_time:.2f} seconds")
                print(f"  Successful results: {successful_results}/{len(domains)}")
                print(f"  Average time per domain: {total_time/len(domains):.2f} seconds")
                print(f"  Throughput: {len(domains)/total_time:.2f} domains/second")
                
                return {
                    "method": "job_queue",
                    "total_time": total_time,
                    "successful_results": successful_results,
                    "total_domains": len(domains),
                    "avg_time_per_domain": total_time/len(domains),
                    "throughput": len(domains)/total_time,
                    "job_id": job_id
                }
            else:
                print(f"- Failed to get job results: {results_response.status_code}")
                return {"method": "job_queue", "error": "Failed to get results"}
        else:
            print(f"- Job queue processing timed out")
            return {"method": "job_queue", "error": "Timeout"}
            
    except requests.exceptions.RequestException as e:
        print(f"- Job queue processing request failed: {e}")
        return {"method": "job_queue", "error": str(e)}

def get_performance_metrics():
    """Get current performance metrics from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/performance", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get performance metrics: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to get performance metrics: {e}")
        return None

def compare_results(results: List[Dict[str, Any]]):
    """Compare performance results"""
    print(f"\n{'=' * 60}")
    print("PERFORMANCE COMPARISON RESULTS")
    print(f"{'=' * 60}")
    
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        print("No successful test results to compare")
        return
    
    print(f"{'Method':<15} {'Time(s)':<10} {'Success':<10} {'Avg/Domain':<12} {'Throughput':<12}")
    print("-" * 60)
    
    fastest_time = min(r['total_time'] for r in valid_results)
    highest_throughput = max(r['throughput'] for r in valid_results)
    
    for result in valid_results:
        method = result['method']
        time_str = f"{result['total_time']:.2f}"
        success_str = f"{result['successful_results']}/{result['total_domains']}"
        avg_str = f"{result['avg_time_per_domain']:.2f}s"
        throughput_str = f"{result['throughput']:.2f}/s"
        
        # Highlight best performers
        if result['total_time'] == fastest_time:
            time_str += " *"
        if result['throughput'] == highest_throughput:
            throughput_str += " *"
        
        print(f"{method:<15} {time_str:<10} {success_str:<10} {avg_str:<12} {throughput_str:<12}")
    
    print("\n* = Best performer")
    
    # Calculate improvements
    if len(valid_results) > 1:
        batch_result = next((r for r in valid_results if r['method'] == 'batch'), None)
        parallel_result = next((r for r in valid_results if r['method'] == 'parallel'), None)
        job_result = next((r for r in valid_results if r['method'] == 'job_queue'), None)
        
        print(f"\nPERFORMANCE IMPROVEMENTS:")
        
        if batch_result and parallel_result:
            time_improvement = ((batch_result['total_time'] - parallel_result['total_time']) / batch_result['total_time']) * 100
            throughput_improvement = ((parallel_result['throughput'] - batch_result['throughput']) / batch_result['throughput']) * 100
            print(f"  Parallel vs Batch: {time_improvement:+.1f}% time, {throughput_improvement:+.1f}% throughput")
        
        if batch_result and job_result:
            time_improvement = ((batch_result['total_time'] - job_result['total_time']) / batch_result['total_time']) * 100
            throughput_improvement = ((job_result['throughput'] - batch_result['throughput']) / batch_result['throughput']) * 100
            print(f"  Job Queue vs Batch: {time_improvement:+.1f}% time, {throughput_improvement:+.1f}% throughput")

def main():
    """Run performance tests"""
    print("🚀 Website Analysis API - Parallel Performance Test")
    print("=" * 60)
    
    # Check API health
    if not test_api_health():
        return
    
    # Get initial performance metrics
    print(f"\n=== Initial Performance Metrics ===")
    metrics = get_performance_metrics()
    if metrics:
        print(f"Rate Limiter: {metrics.get('rate_limiter', {}).get('max_concurrent', 'N/A')} max concurrent")
        print(f"Session Pool: {metrics.get('session_pool', {}).get('pool_size', 'N/A')} sessions")
        if 'worker_queue' in metrics:
            wq = metrics['worker_queue']
            print(f"Worker Queue: {wq.get('total_workers', 'N/A')} workers, {wq.get('jobs_processed', 0)} jobs processed")
    
    # Use subset of test domains for faster testing
    test_domains = TEST_DOMAINS[:10]  # First 10 domains
    print(f"\nTesting with {len(test_domains)} domains: {', '.join(test_domains)}")
    
    results = []
    
    # Test 1: Traditional batch processing
    batch_result = test_traditional_batch_processing(test_domains, batch_size=5)
    results.append(batch_result)
    
    # Small delay between tests
    print("Waiting 3 seconds before next test...")
    time.sleep(3)
    
    # Test 2: New parallel processing
    parallel_result = test_parallel_processing(test_domains, batch_size=10)
    results.append(parallel_result)
    
    # Small delay between tests
    print("Waiting 3 seconds before next test...")
    time.sleep(3)
    
    # Test 3: Job queue processing
    job_result = test_job_queue_processing(test_domains, batch_size=10)
    results.append(job_result)
    
    # Compare results
    compare_results(results)
    
    # Final performance metrics
    print(f"\n=== Final Performance Metrics ===")
    final_metrics = get_performance_metrics()
    if final_metrics and 'worker_queue' in final_metrics:
        wq = final_metrics['worker_queue']
        print(f"Jobs processed: {wq.get('jobs_processed', 0)}")
        print(f"Jobs failed: {wq.get('jobs_failed', 0)}")
        print(f"Total domains processed: {wq.get('total_domains_processed', 0)}")
        print(f"Average processing time: {wq.get('average_processing_time', 0):.2f}s per job")
    
    print(f"\n✅ Performance testing completed!")
    print(f"🔗 View detailed API documentation at: {API_BASE_URL}/docs")

if __name__ == "__main__":
    main()