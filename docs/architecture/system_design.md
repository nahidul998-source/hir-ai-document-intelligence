# HIR Enterprise AI Document Intelligence Architecture

## High-Level Architecture

The platform follows a Domain-Driven Design (DDD) and Clean Architecture pattern, highly distributed via event sourcing.

### Core Engines
1. **Metadata Engine**: Manages project schemas and prompt registries.
2. **AI Engine**: Executes OCR, layout detection, and LLM extractions (hosted in `ai-worker`).
3. **Workflow Engine**: Orchestrates the state transitions (Upload -> Extract -> Review -> ERP Push).
4. **Validation & Knowledge Engine**: Evaluates extracted data against Master Data (ERP Cache) and Garment Industry business rules (e.g., BOM completeness, GSM standards, Size Ratios).
5. **Integration Engine**: Bridges the platform to external ERPs/PLMs (hosted in `erp-worker`).

## Asynchronous Communication
All decoupled services communicate via RabbitMQ.
- `ai_extraction_queue`: Document IDs awaiting AI processing.
- `erp_push_queue`: Approved review sessions ready for PLM/ERP ingestion.
- **DLX/DLQ**: All queues have Dead Letter Exchanges configured to catch processing failures, ensuring no data loss.

## Production Topology
- **Backend API**: FastAPI (Python 3.11), asynchronous, serving the frontend.
- **Database**: PostgreSQL with pgvector for future RAG expansions.
- **Frontend**: React + Vite, serving the highly dynamic Review Workspace.
- **Workers**: Scalable python workers consuming AMQP messages.
