## 2. Real-Time Delivery Approach

To ensure notifications appear instantly without forcing the front-end to constantly spam the server with HTTP requests, we will use a **WebSocket (`ws://`)** connection.

### WebSocket Connection Contract
* **Protocol:** `ws://` (or secure `wss://`)
* **Endpoint:** `ws://api.example.com/v1/notifications/stream`
* **Authentication:** Handled during the initial connection handshake by passing the user's `Bearer token` in the query parameters or connection headers.

### Real-Time Event Payload (JSON)
When a new notification is generated on the backend, the server will instantly push this lightweight JSON payload across the open WebSocket channel to the client:

```json
{
  "event": "notification_received",
  "data": {
    "id": "notif_01H7X8Z123",
    "title": "New Placement Offer",
    "message": "You have been shortlisted for the Software Engineer role at TechCorp!",
    "type": "Placement",
    "created_at": "2026-07-01T12:30:00Z"
  }
}




# Stage 2: Database Design & Reliability

## 1. Storage Choice & Justification
* **Recommended Database:** **PostgreSQL (Relational/SQL DB)**
* **Justification:** * **Data Integrity:** Notifications require strict status tracking (`is_read` true/false). A relational database guarantees ACID compliance, ensuring that when a student clicks a notification, its state updates accurately across all their connected devices instantly without sync delay.
  * **Relational Mapping:** It makes it straightforward to map relationships between a specific `Student` account and their respective list of `Notifications` using Foreign Keys.

## 2. Relational Database Schema Design
Here are the structured SQL tables to cleanly persist the notifications and support fast relational queries:

```sql
-- Represents the students receiving the alerts
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Represents the notification types matching the system requirement enums
CREATE TYPE notification_enum AS ENUM ('Event', 'Result', 'Placement');

-- Represents the notifications ledger
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    notification_type notification_enum NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



# Stage 4: High-Load Read Optimization (Caching)

## 1. Proposed Solution: In-Memory Caching (Redis)
To eliminate redundant, heavy database queries on every page load, a caching layer using **Redis** will be placed in front of our primary database. 

## 2. Implementation Strategy
* **Cache-Aside Pattern:** When a student loads the page, the application first checks Redis using a unique key (`user:notifications:unread:<student_id>`). 
  * **Cache Hit:** If data is found, it returns instantly without hitting the database.
  * **Cache Miss:** If not found, the app queries PostgreSQL, saves the result back to Redis with a Time-To-Live (TTL) configuration (e.g., 5 minutes), and returns the payload.
* **Cache Invalidation:** When a new notification is generated or marked as read, the cache key for that specific student is deleted or updated to maintain data consistency.

## 3. Trade-offs Analysis
* **Pros:** Drastically reduces database CPU utilization; drops API response latency down to sub-milliseconds ($<2\text{ms}$); protects the system from crashing during high concurrent student traffic.
* **Cons:** Introduces slight architectural complexity; risks temporary stale data reads if cache invalidation logic fails.





# Stage 5: Mass Broadcasting Optimization

## 1. Flaws in the Synchronous Implementation
The current pseudocode approach uses a sequential loop to execute network operations (sending emails/in-app push messages) one-by-one. For 50,000 students:
* If a single email API call takes just 100ms, the entire function would take **5,000 seconds (nearly 1.4 hours)** to finish.
* This will cause an HTTP timeout error, freeze the application thread, and drop notifications for subsequent students if the process crashes midway.

## 2. Optimized Architectural Pattern
To make this reliable and near-instantaneous for the HR administrative user, we must move the loop into a background asynchronous worker architecture using a fan-out pattern:



# Stage 6: Priority Inbox Algorithm & Implementation

## 1. Algorithmic Approach
To compute the priority index without a database sorting operation, the application fetches the system array stream and processes sorting inside memory runtime space. 
* **Compound Tuple Sort Key:** The sorting engine uses a multi-layered priority evaluation function: `(-weight, -timestamp)`.
* This ensures Python automatically clusters all high-value notifications (`Placement` first, then `Result`, then `Event`), while instantly handling inner ties by placing the most recent timestamps at the top of each priority block.

## 2. Production Scalability & Stream Maintenance
As new notifications stream into the server space over time:
* Instead of running a full array $O(N \log N)$ sort every time a single item arrives, we can maintain the array dynamically using a **Min-Heap** data structure limited strictly to a capacity of size `n` (10).
* For every incoming record, we compare its weight/recency value against the smallest item currently stored in the heap. This lowers insert and stream management complexity down to an incredibly lightweight **$O(\log n)$**, making real-time memory handling trivial.




# Stage 7: Front-End Architecture & Production Standards

## 1. System Middleware & Observability Integration
To ensure the system satisfies high-reliability standards, an isolated logging middleware is hooked directly into the HTTP call stack tracking lifecycle activities:
* **Trace-ID Injection:** Every incoming client request receives a unique tracking correlation ID via headers. If an edge failure happens downstream, logs can be isolated instantly.
* **Metrics Tracked:** Latency timings, status breakdowns, connection failure spikes on WebSockets, and data throughput volume.

## 2. Edge-Case Resolution Protocols
* **Stale WebSocket Dropouts:** If the front-end notices socket ping-pong handshakes dropping, it instantly downshifts back to a graceful degradation model, initiating low-frequency fallback polling of the REST endpoint while quietly establishing reconnect logic behind the scenes.
* **Malformed Payloads:** If the client UI parses an unmapped enum value, a safe default rendering fallback component handles the block safely instead of breaking the browser layout page.

## 3. UI Filtering and Custom Display Control
On the separate configurations interface dashboard, options allow filtering views directly. The system coordinates query constraints natively by injecting parameterized query string arguments back to the Stage 1 REST API layer (e.g., `GET /v1/notifications?type=Placement&limit=10`).