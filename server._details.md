# FedEx IIT – Server Specification for 100–200 Users

## 1. Project Overview

This document describes the recommended server infrastructure for hosting the FedEx IIT application for approximately 100–200 users.

The proposed infrastructure is designed to provide:
- Reliable application performance
- Secure user authentication
- Efficient database operations
- Support for concurrent users
- Automated backups
- Future scalability
- Monitoring and maintenance

## 2. Recommended Server Configuration

| Component | Recommended Specification |
|---|---|
| CPU | 8 vCPU |
| RAM | 16 GB |
| Storage | 250 GB NVMe SSD |
| Operating System | Ubuntu Server 24.04 LTS |
| Architecture | 64-bit |
| Network | Minimum 1 Gbps |
| Bandwidth | 5 TB/month or higher |
| Public IP | 1 Static IPv4 |
| Users | 100–200 registered users |
| Deployment | Cloud VPS or dedicated cloud server |

**Recommended production configuration:** 8 vCPU, 16 GB RAM, and 250 GB NVMe storage.

For heavier workloads or higher concurrency, consider 16 vCPU and 32 GB RAM.

## 3. Software Requirements

| Software | Recommended Version | Purpose |
|---|---|---|
| Ubuntu Server | 24.04 LTS | Operating system |
| Python | 3.x | Application runtime |
| PostgreSQL | 16 | Database |
| Nginx | Latest stable | Reverse proxy |
| Redis | Latest stable | Caching and background jobs, if required |
| Git | Latest stable | Source code management |
| SSL | Let's Encrypt | HTTPS security |
| Docker | Latest stable | Optional containerization |

Application-specific software versions must be confirmed against the repository's dependency files before deployment.

## 4. Server Architecture

    INTERNET
       |
    DOMAIN NAME
       |
    NGINX REVERSE PROXY
       |
    APPLICATION SERVER
       |
       |-------------------|
       |                   |
    BACKGROUND JOBS     POSTGRESQL
       |                   |
      REDIS              DATABASE
       |
    FILE STORAGE
       |
    BACKUP STORAGE

## 5. CPU Requirements

| Workload | CPU Requirement |
|---|---|
| Application processing | 4 vCPU |
| Database operations | 2 vCPU |
| Background tasks | 1 vCPU |
| Operating system and services | 1 vCPU |
| **Total** | **8 vCPU** |

CPU requirements depend on application complexity, database queries, file processing, and concurrent usage.

## 6. RAM Requirements

| Component | Estimated RAM |
|---|---:|
| Operating system | 1 GB |
| Application server | 5 GB |
| PostgreSQL database | 4 GB |
| Nginx and supporting services | 1 GB |
| Background workers and caching | 2 GB |
| System overhead and available memory | 3 GB |
| **Total** | **16 GB** |

The actual memory allocation should be adjusted after load testing.

## 7. Storage Requirements

| Storage Component | Recommended Size |
|---|---:|
| Operating system | 30 GB |
| Application files | 20 GB |
| Database | 80 GB |
| Uploaded files and documents | 70 GB |
| Logs and temporary files | 20 GB |
| Free space and growth | 30 GB |
| **Total** | **250 GB** |

Use NVMe SSD storage for better database and application performance.

Keep backups outside the main application server.

## 8. Database Configuration

Recommended database: PostgreSQL 16.

Suggested initial configuration for a 16 GB RAM server:

    max_connections = 150
    shared_buffers = 4GB
    effective_cache_size = 10GB
    maintenance_work_mem = 512MB
    work_mem = 16MB
    wal_buffers = 16MB
    checkpoint_completion_target = 0.9
    random_page_cost = 1.1

These are starting values, not universal production settings. Review them based on actual query patterns, connection pooling, and workload testing.

Recommended database practices:

- Enable automated database backups.
- Configure database monitoring.
- Use connection pooling where appropriate.
- Create indexes for frequently queried columns.
- Review slow queries regularly.
- Restrict database access to trusted services.
- Keep database credentials secure.

## 9. Application Server Configuration

The application server should support:

- Multiple worker processes.
- Background job processing.
- Request timeouts.
- Application logging.
- Health checks.
- Graceful restarts.
- Error monitoring.

The exact worker configuration depends on the application framework and its process model.

For an Odoo-based deployment, worker sizing must follow Odoo's deployment recommendations and be validated against actual CPU and memory usage.

## 10. Nginx Configuration

Nginx should act as the reverse proxy in front of the application.

Example configuration:

    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;

        location / {
            proxy_pass http://127.0.0.1:8069;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }

Configure HTTPS using a valid SSL certificate before exposing the production application.

## 11. Network Requirements

| Requirement | Specification |
|---|---|
| Public IP | Static IPv4 |
| Network speed | 1 Gbps preferred |
| Monthly bandwidth | 5 TB or higher |
| HTTP port | 80 |
| HTTPS port | 443 |
| SSH port | 22, restricted to administrator IPs |
| Database port | Private network only |
| Application port | Private network only |

Never expose PostgreSQL directly to the public internet.

## 12. Security Requirements

The production server must implement the following security controls:

- SSH key-based authentication.
- Disable password-based SSH login where practical.
- Disable root SSH login.
- Configure a firewall.
- Allow only necessary ports.
- Install security updates regularly.
- Configure HTTPS.
- Use strong database passwords.
- Store secrets in environment variables or a secrets manager.
- Restrict database access.
- Configure rate limiting where appropriate.
- Monitor suspicious login attempts.
- Maintain application and operating system logs.
- Use least-privilege access permissions.

## 13. Backup Strategy

Recommended backup schedule:

| Backup Type | Frequency |
|---|---|
| Database backup | Daily |
| Application configuration | Daily |
| Uploaded files | Daily |
| Full backup | Weekly |
| Off-site backup | Daily |
| Backup restoration test | Monthly |

Recommended backup retention:

- Daily backups: 14 days
- Weekly backups: 8 weeks
- Monthly backups: 6 months

Backups should be encrypted and stored separately from the production server.

Suggested recovery objectives:

| Metric | Initial Target |
|---|---|
| Recovery Point Objective (RPO) | 24 hours |
| Recovery Time Objective (RTO) | 4–8 hours |

These targets should be reviewed according to business requirements.

## 14. Monitoring Requirements

Monitor the following metrics:

| Metric | Monitoring Requirement |
|---|---|
| CPU usage | Continuous |
| RAM usage | Continuous |
| Disk usage | Continuous |
| Database performance | Continuous |
| Application response time | Continuous |
| Network traffic | Continuous |
| Server uptime | Continuous |
| Failed login attempts | Continuous |
| Backup status | Daily |
| SSL certificate expiry | Automated alerts |

Recommended monitoring tools:

- Prometheus
- Grafana
- Netdata
- Uptime Kuma
- PostgreSQL monitoring tools

## 15. Load Testing

Before production deployment, conduct load testing.

Test scenarios:

| Test | Target |
|---|---|
| Registered users | 200 |
| Concurrent users | 50 |
| Higher concurrency test | 100 |
| Peak load test | 150 |
| Stress test | Gradually increase until failure |
| Endurance test | 2–4 hours |

Measure:

- Average response time.
- 95th percentile response time.
- Requests per second.
- CPU utilization.
- Memory utilization.
- Database connections.
- Database query duration.
- Error rate.

Suggested acceptance criteria:

- No application crashes.
- No database connection exhaustion.
- No unexpected data loss.
- Stable memory consumption.
- Acceptable response times under expected load.
- Successful backup and restoration.

The actual performance capacity must be established through testing with realistic application data and user workflows.

## 16. Deployment Structure

Recommended directory structure:

    /opt/fedex-iit/
        application/
        config/
        logs/
        scripts/
        uploads/
        backups/

Keep application source code, configuration, logs, uploaded files, and backups logically separated.

## 17. Recommended Production Setup

    Operating System: Ubuntu Server 24.04 LTS
    CPU: 8 vCPU
    RAM: 16 GB
    Storage: 250 GB NVMe SSD
    Database: PostgreSQL 16
    Web Server: Nginx
    Application Runtime: As required by repository
    Network: 1 Gbps
    Bandwidth: 5 TB/month or higher
    Public IP: Static IPv4
    SSL: Let's Encrypt
    Backup: Automated daily off-site backups
    Monitoring: Prometheus + Grafana or Netdata
    Firewall: UFW

## 18. Future Scalability

| Users / Workload | Suggested Infrastructure |
|---|---|
| Initial deployment | 8 vCPU, 16 GB RAM |
| Increased usage | 12–16 vCPU, 32 GB RAM |
| Heavy database workload | Separate database server |
| Heavy file uploads | Object storage |
| High availability | Multiple application servers |
| Large-scale deployment | Load balancer and distributed architecture |

Do not scale based only on registered user count. Scale based on measured concurrency, request volume, CPU usage, memory consumption, and database workload.

## 19. Final Recommendation

For a deployment targeting 100–200 users, start with:

**8 vCPU + 16 GB RAM + 250 GB NVMe SSD.**

Use Ubuntu Server 24.04 LTS, PostgreSQL 16, Nginx, HTTPS, automated backups, and server monitoring.

This configuration is a reasonable starting point for a production deployment. Final sizing should be confirmed through dependency verification, realistic load testing, and database performance testing.
