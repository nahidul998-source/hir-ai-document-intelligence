import asyncio
import httpx
import uuid
import time
import argparse

async def upload_document(client: httpx.AsyncClient, i: int):
    """Simulates uploading a mock PDF document to the platform."""
    try:
        # Create a small mock PDF payload in memory
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        files = {"file": (f"mock_doc_{i}.pdf", pdf_content, "application/pdf")}
        
        doc_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/v1/documents/upload/{doc_id}",
            files=files
        )
        if response.status_code in (200, 201):
            return doc_id
        else:
            print(f"Failed upload {i}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error on upload {i}: {e}")
        return None

async def main(concurrent_users: int, total_documents: int):
    print(f"Starting Load Test: {total_documents} documents via {concurrent_users} concurrent workers.")
    
    start_time = time.time()
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as client:
        tasks = []
        for i in range(total_documents):
            tasks.append(upload_document(client, i))
            
            # Batch execution to simulate concurrency limits
            if len(tasks) >= concurrent_users:
                await asyncio.gather(*tasks)
                tasks = []
                
        if tasks:
            await asyncio.gather(*tasks)
            
    duration = time.time() - start_time
    print(f"\n--- Load Test Complete ---")
    print(f"Total Time: {duration:.2f} seconds")
    print(f"Throughput: {total_documents / duration:.2f} docs/sec")
    print("\nPlease check RabbitMQ metrics to verify DLQ and processing queues handled the spike.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HIR Load Tester")
    parser.add_argument("--users", type=int, default=50, help="Concurrent users")
    parser.add_argument("--docs", type=int, default=1000, help="Total documents to upload")
    args = parser.parse_args()
    
    asyncio.run(main(args.users, args.docs))
