FedEx-IIT Repository --- Production Server Infrastructure Specification
Repository:
fedexiitproject-GOAT/FedEx-IIT
Target capacity: 100--200 registered users
Recommended starting deployment: 8 vCPU, 16 GB RAM, 250 GB NVMe
Application: Odoo 18 Community
Important: This is a proposed production sizing and deployment
specification, not a benchmark or certification of the repository.
Actual capacity must be established through staging tests and load
testing.

1. Executive summary
The project is an Odoo 18 Community-based research and project data
management system. Its documented responsibilities include:
1. Centralized identity management for students, faculty and staff.
2. Research project and member management.
3. Document management across personal, project and engagement scopes.
4. Document requirements and automated completion checklists.
5. Project milestones, deliverables and monitoring.
6. Excel/CSV bulk import with validation and duplicate handling.
7. Interactive OWL dashboards, KPIs and global search.
8. Scheduled alerts for overdue milestones, expiring contracts and
   missing documents.
The main architectural implication is that Odoo, PostgreSQL and document
storage must be treated as one production system, with coordinated
backups, access controls and capacity planning.
2. Application architecture
The repository is a single installable Odoo addon named
fedex_repository, rather than a collection of independently deployed
microservices.
2.1 Logical architecture
Users (100–200 accounts)
  Students | Faculty | Coordinators | Management | Administrators
                         |
                         v
              HTTPS / Nginx reverse proxy
        TLS | routing | request limits | static assets
                         |
                         v
                 Odoo 18 application
       +-----------------+--------------------+
       |                 |                    |
  HTTP workers      Cron workers       Import/document
  OWL interface     Scheduled jobs     processing
       |                 |                    |
       +-----------------+--------------------+
                         |
              +----------+-----------+
              |                      |
              v                      v
        PostgreSQL              Odoo filestore
   Records, relations,       Documents, attachments,
   transactions, access      uploaded files, revisions
   rules and metadata
PostgreSQL and the Odoo filestore require coordinated backup and
recovery.
2.2 Repository components and infrastructure implications
  Repository component                 Responsibility          Infrastructure
implication
  models/people.py                   Identity and academic   Relational queries and
profiles                access control

  models/project.py                  Projects, members and   Project and
milestones              relationship queries

  models/document.py                 Document lifecycle and  Filestore capacity and
versioning              I/O

  models/alert.py                    Automated alerts        Scheduled job capacity

  models/master.py                   Centres and master data Reference data

  models/settings.py                 System configuration    Configuration and
administration

  wizard/import_wizard.py            XLSX/CSV processing     CPU, RAM and temporary
storage

  controllers/import_controller.py   Template downloads      HTTP routing

  static/src/js/                     Dashboard and global    Frontend and backend
search                  query performance

  security/                          Access permissions and  Security correctness
record rules            and query overhead

  data/cron.xml                      Scheduled automation    Cron capacity and
scheduling
tests/                             Security, imports,      Release confidence
documents and other
tests
The data model uses res.partner as a shared identity foundation.
Projects connect to centres, members, milestones, documents and
requirements.
2.3 Main resource-intensive areas
1. Document storage: Document uploads and preserved revisions can
   make storage growth more important than the raw account count.
2. PostgreSQL: Dashboard metrics, project relationships,
   record-level access rules and global search depend on database
   performance.
3. Concurrent Odoo workers: 100--200 registered accounts do not
   imply 100--200 simultaneous requests.
4. Excel/CSV imports: Large imports can temporarily consume
   significantly more CPU and RAM than ordinary browsing.
5. Scheduled automation: Alerts, milestone checks and
   document-expiry monitoring must not degrade interactive sessions.
3. Recommended server specification
For 100--200 registered users, the recommended initial production server
is a dedicated Linux VPS or cloud VM with SSD/NVMe storage.
3.1 Recommended production configuration
  Component              Recommendation
  CPU                    8 vCPU
RAM                    16 GB
Storage                250 GB NVMe SSD
Operating system       Ubuntu Server 24.04 LTS
Database               PostgreSQL 16
Application            Odoo 18 Community
Runtime                Python 3.12
Reverse proxy          Nginx
SSL                    Let's Encrypt / Certbot
Process management     systemd
Initial HTTP workers   6
Initial cron workers   2

This is a starting point for approximately 25--50 active concurrent
users, subject to load testing. It is not a guarantee that the server
will support that concurrency for every workload.
3.2 Three sizing options
  Specification              Minimum        Recommended       Growth-ready
  vCPU                             4                  8             12--16

  RAM                           8 GB              16 GB              32 GB

  NVMe SSD                    100 GB             250 GB             500 GB

  Registered                100--200           100--200               200+
users                                                 

  Planning                    10--20             25--50            50--100
concurrency                                           

  Architecture         Single server      Single server     Split services
Suitability            Light usage         Production    Higher workload
starting point
Recommendation: Start with 8 vCPU, 16 GB RAM and 250 GB NVMe. Avoid
starting with only 4 GB RAM for this workload because Odoo, PostgreSQL,
Python workers, imports and file processing need memory headroom.

The concurrency values are planning assumptions, not measured repository
capacity.
4. Odoo worker configuration
Odoo supports multiprocessing workers for production. Its documentation
provides worker-sizing guidelines, including an approximate worker
requirement of CPU cores × 2 + 1 and a rough planning ratio of one
worker per six concurrent users. These are sizing guidelines, not
guarantees.
4.1 Proposed initial worker allocation
  Setting                             Initial value
  HTTP workers                                    6
Cron workers                                    2
Gevent/WebSocket listener     1 dedicated process

The six HTTP workers are a conservative starting point for an 8-vCPU
server. Heavy imports and document operations can occupy workers for
longer than ordinary page requests.
4.2 Suggested odoo.conf
[options]

; Database
db_host = False
db_port = False
db_user = odoo
db_password = CHANGE_TO_STRONG_PASSWORD
db_name = fedex_repository
list_db = False

; Addons
addons_path = /opt/odoo/odoo18/addons,/opt/odoo/custom_addons

; Production server
http_interface = 127.0.0.1
http_port = 8069
gevent_port = 8072
proxy_mode = True

; Workers
workers = 6
max_cron_threads = 2

; Memory limits per worker
limit_memory_soft = 1610612736
limit_memory_hard = 2147483648

; Request management
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200

; Database connection
db_maxconn = 64

; Logging
logfile = /var/log/odoo/odoo.log
log_level = info

; Security
admin_passwd = CHANGE_TO_RANDOM_MASTER_PASSWORD
Configuration notes:
- db_host = False uses the local PostgreSQL socket. This is suitable
  when both services are on the same server.
- proxy_mode = True is required when Odoo is behind a correctly
  configured trusted reverse proxy.
- Memory limits are per worker, not a total RAM reservation.
- Keep the Odoo database user non-superuser.
- The Odoo master password is different from the application
  administrator password.
- Do not expose ports 8069, 8072 or 5432 publicly.
- Confirm the exact Odoo 18 configuration parameter names against the
  installed build before deployment.
5. Hardware and storage allocation
5.1 RAM planning budget
Illustrative budget for a 16 GB combined application/database server:

  Component                                   Planning budget
  Odoo processes                                         5 GB
PostgreSQL                                             4 GB
Ubuntu and Nginx                                       2 GB
Import and temporary workload allowance                2 GB
Safety headroom                                        3 GB
Total                                         16 GB

These are planning budgets. Linux page cache, PostgreSQL shared memory
and worker memory overlap in actual memory accounting; this is not a
literal fixed allocation.
5.2 Disk planning budget
  Storage area                      Suggested allocation
  Ubuntu and system packages                       25 GB
Odoo source and custom addons                    10 GB
PostgreSQL database and WAL                      40 GB
Odoo filestore                                  150 GB
Logs and temporary files                         10 GB
Free capacity                                    15 GB
Total                                   250 GB

Keep PostgreSQL data and the Odoo filestore logically separate, even if
they initially reside on the same physical NVMe drive.

The document archive is important because replacing a document can
preserve historical revisions. Plan for cumulative storage growth, not
just current uploaded file sizes.
5.3 Example storage growth calculation
Use:

Storage (MB) = users × documents per user per year × average document size (MB) × years

Example:

  Parameter                       Example
  Users                               200
Documents per user per year          20
Average document size              2 MB
Retention                       5 years
Calculated document storage       40 GB

This excludes additional versions, operational overhead and backups. A
150 GB filestore allocation is a starting allowance, not a lifetime
capacity estimate.
6. PostgreSQL specification
Recommended version: PostgreSQL 16, subject to compatibility testing
with the selected Odoo 18 build and deployment packages.

The repository requires PostgreSQL 14 or newer.
6.1 Initial database configuration
For a 16 GB combined application/database server:

  Parameter                                           Initial value
  shared_buffers                                             4 GB
effective_cache_size                                      10 GB
work_mem                                                  16 MB
maintenance_work_mem                                     512 MB
max_connections                                             100
wal_buffers                                               16 MB
min_wal_size                                               1 GB
max_wal_size                                               4 GB
checkpoint_completion_target                                0.9
random_page_cost                 1.1 (NVMe starting assumption)

These are tuning starting points, not universal optimal values. In
particular, work_mem is allocated per sort/hash operation and can
multiply across concurrent queries.
6.2 Database requirements
1. Use a dedicated PostgreSQL database for production.
2. Create a restricted PostgreSQL account for Odoo.
3. Keep PostgreSQL accessible only locally or over a private network.
4. Enable regular database vacuuming and analyze operations.
5. Monitor database size and transaction performance.
6. Monitor slow SQL queries.
7. Verify indexes for frequently queried fields.
8. Benchmark dashboard and global-search queries.
9. Back up PostgreSQL and the Odoo filestore together.
6.3 Dashboard and global-search performance
The application includes project-code, project-title, student,
supervisor and document-title search, plus dashboard KPIs and grouping
by centre, vertical, stage and sponsor.

Benchmark searches across 10,000--50,000 records and dashboard
operations with realistic access-control rules. This is a proposed test
dataset, not an estimate of the repository's current database size.
7. Reverse proxy and networking
Use Nginx in front of Odoo.
7.1 Public and internal ports
  Service                   Port Exposure
  HTTP                        80 Public; redirect to HTTPS
HTTPS                      443 Public
Odoo HTTP                 8069 Internal only
Odoo WebSocket/gevent     8072 Internal only
PostgreSQL                5432 Local/private only
SSH                         22 Restricted administrator IPs or VPN

Database and Odoo backend ports must not be publicly reachable.
7.2 Nginx requirements
- TLS certificate using Let's Encrypt.
- HTTP-to-HTTPS redirection.
- Reverse proxy to Odoo port 8069.
- WebSocket routing to port 8072.
- Appropriate connection and read timeouts.
- Request-body limit aligned with the application's configured 25 MB
  file upload limit.
- Gzip compression for text-based assets.
- Security headers.
- Access and error logs.
- Rate limiting on authentication endpoints.
For a 25 MB upload limit, set Nginx client_max_body_size to
approximately 32m as a starting point and verify that Odoo's
configured limit and request encoding are compatible.
8. Document storage and file-upload infrastructure
The document model uses:
file = fields.Binary(attachment=True, required=True)
Uploaded binary files are handled through Odoo's attachment
infrastructure and are normally stored in the Odoo filestore rather than
directly in PostgreSQL rows.

The repository's documented document functionality includes:
- Configurable maximum upload size, default 25 MB.
- Configurable allowed file extensions.
- Person, Project and Engagement document scopes.
- Document requirements and checklists.
- Document replacement and revision tracking.
- Automatic checklist synchronization.
8.1 Recommended document infrastructure
  Component                      Recommendation
  Primary storage                Local NVMe filestore
Initial filestore allocation   150 GB
Upload limit                   25 MB
Backup                         Separate remote storage
Document access                Odoo authenticated routes
File permissions               Restricted Odoo service account
Malware scanning               ClamAV or equivalent
Archive retention              Preserve previous versions
Storage monitoring             Alert at 70%, 80% and 90%

Security consideration: The repository's allowed extensions include
ZIP, Python and Jupyter Notebook files. Extension checking alone does
not establish that a file is safe. Use malware scanning, MIME-type
validation, archive inspection and strict download permissions.

Do not expose the filestore directory directly through Nginx.
9. Backup and disaster recovery
The system contains academic records, identity information, project
documentation and historical files. Backups are mandatory
infrastructure.
9.1 Backup architecture
Production server
  PostgreSQL + Odoo filestore
             |
             v
Automated backup process
  Database backup + filestore + configuration
             |
             v
Separate backup storage
  Encrypted + versioned + access restricted
             |
             v
Disaster recovery environment
  Restore database and matching filestore
9.2 Proposed backup schedule
  Backup                     Frequency    Retention
  PostgreSQL full backup     Daily        30 days
Filestore backup           Daily        30 days
PostgreSQL WAL archiving   Continuous   7--14 days
Weekly backup              Weekly       12 weeks
Monthly archive            Monthly      12 months
Recovery test              Monthly      Permanent test record

Retention must be reconciled with institutional data-retention policies.
9.3 Recovery targets
  Objective                          Proposed target
  RPO (maximum targeted data loss)   1 hour
RTO (target service restoration)   4 hours

These are proposed service objectives, not demonstrated recovery times.
They require tested WAL archiving, off-site backups, sufficient restore
infrastructure and an operational recovery procedure.

Critical: A PostgreSQL backup without the corresponding filestore is
not a complete recovery of this application. Keep database and file
backups consistent, preferably using a coordinated snapshot or a
documented backup procedure.
10. Security specification
The repository documents six distinct security groups and centre-based
access restrictions. This is a core application requirement.
10.1 Application-level roles
  Role                 Intended permission
  Administrator        Full system control
Repository Manager   All-centre management
Coordinator          Assigned-centre access
Faculty              Assigned project access
Student              Own and assigned records
Management           Global read-only access

Verify actual access rights and record rules in staging; role labels
alone do not prove that access is correctly enforced.
10.2 Infrastructure security checklist
  Requirement             Implementation
  HTTPS                   Mandatory
SSH                     Key-based authentication
Firewall                UFW or cloud firewall
Database access         Localhost/private network only
Odoo database manager   Disabled/hardened
Application admin       Strong unique credentials
Master password         Strong random secret
Backups                 Encrypted off-site
File uploads            Validation and malware scanning
Login protection        Rate limiting and fail2ban
OS security             Automatic security updates
Monitoring              Login and service logs
Admin access            Restricted IP/VPN
Secrets                 Environment-protected or restricted config files
10.3 Institutional privacy considerations
Role-based access controls do not by themselves establish legal
compliance.

For an institutional deployment, establish:
- Data ownership and processing responsibilities.
- Student-data access policies.
- Retention and deletion policies.
- Incident response procedures.
- Access audit trails.
- Backup deletion and retention procedures.
- Appropriate institutional approval for hosting and external storage.
Restrict access to identity documents, CGPA, student status and personal
information.
11. Deployment topology options
Option A --- Single-server deployment
Recommended initially.

  Service         Location
  Nginx           Same VM
Odoo 18         Same VM
PostgreSQL 16   Same VM
Filestore       Same VM / separate volume
Backup          External storage

Advantages
- Lower cost.
- Simpler management.
- Low database network latency.
- Suitable as an initial deployment for 100--200 registered users,
  subject to testing.
Disadvantages
- Services share CPU and RAM.
- A server failure affects the entire application.
- Database and application workloads compete.
Option B --- Separate application and database servers
  Server        Suggested specification
  Application   8 vCPU, 16 GB RAM
Database      4--8 vCPU, 16 GB RAM
Storage       250--500 GB NVMe, based on document growth
Backup        Separate object storage

Advantages
- Database performance is isolated.
- Application scaling is easier.
- Maintenance can be performed more independently.
- Better separation of security boundaries.
Disadvantages
- Higher recurring cost.
- More configuration and monitoring.
- Requires secure private networking.
Recommendation: Start with Option A at 8 vCPU / 16 GB RAM. Move to
Option B when measured database load, document traffic or CPU/RAM
utilization justifies it.

A separate database server does not automatically provide high
availability; redundancy and failover require additional engineering.
12. Deployment software stack
  Layer                Software
  Operating system     Ubuntu Server 24.04 LTS
Web server           Nginx
Application          Odoo 18 Community
Runtime              Python 3.12
Database             PostgreSQL 16
Excel processing     openpyxl
SSL                  Let's Encrypt
Process management   systemd
Firewall             UFW
Monitoring           Prometheus + Grafana or Netdata
Log management       journald / logrotate
Malware scanning     ClamAV
Backup               pgBackRest or equivalent PostgreSQL-aware tooling

The addon manifest documents dependencies on Odoo's base, mail,
web and contacts modules, and Python openpyxl.
12.1 Suggested filesystem layout
/opt/
└── odoo/
    ├── odoo18/
    └── custom_addons/
        └── fedex_repository/

/etc/
└── odoo/
    └── odoo.conf

/var/lib/
└── odoo/
    └── filestore/

/var/log/
└── odoo/
    └── odoo.log

/var/backups/
└── fedex-repository/
    ├── database/
    ├── filestore/
    └── configuration/
Keep production secrets out of Git and do not store backup credentials
in publicly readable files.
13. Code-level performance considerations
The following areas deserve production performance testing. They are not
necessarily defects, but they may become bottlenecks as record counts
and usage increase.
13.1 Daily alert processing
The alert cron performs operations including:
project_model = Project.search([])
project_model._compute_days()

req_model._sync_requirements(project_model)
It subsequently processes projects and members to generate alerts.

Potential concern: As the number of projects and document
requirements grows, this scheduled job may become expensive.

Recommended improvements:
- Process records in batches.
- Avoid unnecessary full-table searches.
- Add appropriate indexes.
- Avoid repeated searches inside loops.
- Track cron execution time.
- Ensure alert generation is idempotent.
- Avoid overlapping long-running scheduled jobs.
13.2 Document checklist synchronization
The _sync_requirements() method in models/document.py handles
multiple owners, profiles, mandatory document types and document
lookups.

Repeated searches, including profile search_count() operations inside
loops, are worth investigating.

Recommended improvements:
- Batched queries.
- Grouped lookups.
- Efficient recordset operations.
- Database-level uniqueness constraints.
- Performance tests for bulk imports and document replacement.
13.3 Global dashboard
Avoid recalculating every KPI independently on every browser refresh if
record counts grow substantially.

Recommended improvements:
- Optimized grouped database queries.
- Appropriate database indexes.
- Pagination for large result sets.
- Caching where data freshness permits.
- Monitoring query execution times.
13.4 Import engine
The importer has a two-phase validation and confirmation workflow.

  Import size   Test purpose
  100 rows      Normal operation
500 rows      Moderate bulk import
1,000 rows    Production scenario
5,000 rows    Stress scenario
10,000 rows   Upper-bound performance investigation

Ensure imports do not make ordinary users experience slow dashboards or
timeouts.
14. Load testing specification
Before going live, perform load testing. The goal is to determine how
many people can use the application simultaneously, not merely whether
200 accounts can log in.
14.1 Proposed test scenarios
  Scenario     Concurrent users Activity
  Normal                     20 Login and browsing
Moderate                   40 Dashboard and project search
Busy                       60 Search, documents and project updates
Peak                      100 Mixed application usage
Stress                    150 Mixed requests and uploads

These are proposed test levels, not expected production capacity.
14.2 Example 100-user workload distribution
  Activity                                 Simulated users
  Dashboard and analytics                               20
Project browsing and editing                          30
Document uploads and downloads                        20
Global search                                         15
Import and administrative operations                   5
General navigation                                    10
Total                                        100
14.3 Proposed performance acceptance criteria
  Metric                                               Target
  Normal page response, p95                   Under 2 seconds
Search response, p95                        Under 2 seconds
Dashboard response, p95                     Under 3 seconds
Ordinary database query, p95                   Under 500 ms
CPU during sustained normal load                  Under 75%
Memory utilization                                Under 85%
Disk utilization                                  Under 80%
HTTP 5xx errors                                  Below 0.1%
Failed login/session operations      No unexpected failures

For imports, uploads and large reports, define separate
operation-specific timing targets rather than applying ordinary
page-load thresholds.
14.4 Recommended testing tools
- Locust --- simulate users.
- k6 --- HTTP load testing.
- pg_stat_statements
  --- identify expensive SQL.
- Prometheus --- metrics collection.
- Grafana --- monitoring dashboards.
Use Locust for realistic Odoo workflows because the application uses
authenticated sessions and multiple interconnected operations.
15. Monitoring and maintenance
15.1 Essential monitoring
  Metric                   Warning threshold
  CPU                      Above 80% for 5 minutes
RAM                      Above 85%
Disk                     Above 80%
Disk I/O wait            Sustained elevated wait
PostgreSQL connections   Above 80% of configured maximum
Odoo worker restarts     Repeated unexpected restart
Failed HTTP requests     Above 1%
Backup failures          Any failure
SSL expiry               Less than 14 days
Filestore capacity       Above 80%
15.2 Monitoring dashboard categories
1. Infrastructure: CPU, RAM, disk, network and uptime.
2. Odoo: Worker utilization, response times, errors and cron
   execution.
3. PostgreSQL: Connections, slow queries, locks, database size and
   cache behavior.
4. Documents: Filestore usage, upload failures, backup status and
   storage growth.
15.3 Maintenance schedule
  Frequency              Maintenance
  Daily                  Backup verification and error-log review
Weekly                 Security updates and disk review
Monthly                Recovery testing and database analysis
Quarterly              Access audit and dependency updates
Before every release   Staging tests and rollback preparation
16. Production deployment procedure
1. Provision server: Create an Ubuntu 24.04 VM with 8 vCPU, 16 GB
   RAM and 250 GB NVMe.
2. Secure operating system: Configure SSH keys, UFW, administrator
   accounts, security updates and time synchronization.
3. Install PostgreSQL 16: Create the production database and
   restricted Odoo database user.
4. Install Odoo 18: Install Python 3.12, Odoo dependencies and
   required Python packages.
5. Install FedEx repository addon: Place the repository in the
   custom addons directory and install fedex_repository.
6. Configure production workers: Set multiprocessing, memory
   limits, cron workers and logging.
7. Configure Nginx and HTTPS: Set up the domain, TLS certificate,
   proxy routing and WebSocket handling.
8. Configure storage and backups: Set up filestore permissions,
   remote backup and backup verification.
9. Configure institutional users: Create roles, centres, user
   accounts and access permissions.
10. Run staging tests: Test imports, document uploads, replacements,
    alerts, dashboards and record-level access.
11. Perform load testing: Test at 20, 40, 60 and 100 concurrent
    users, then investigate bottlenecks.
12. Go live: Perform final backup, production installation
    verification and monitoring setup.
16.1 Initial addon installation command
After creating the database and configuring the addon path:
sudo -u odoo /opt/odoo/odoo18/odoo-bin \
    -c /etc/odoo/odoo.conf \
    -d fedex_repository \
    -i fedex_repository \
    --without-demo=all \
    --stop-after-init
16.2 Subsequent module upgrade command
sudo -u odoo /opt/odoo/odoo18/odoo-bin \
    -c /etc/odoo/odoo.conf \
    -d fedex_repository \
    -u fedex_repository \
    --stop-after-init
Always back up the database and filestore before an upgrade, and test
upgrades in staging first.
17. Repository production-readiness assessment
Distinguish between what the repository documents and what still needs
validation.
  Area                                Assessment
  Odoo 18 compatibility declaration   Documented

  Relational architecture             Documented

  User roles and access control       Implemented and documented

  Document lifecycle                  Implemented

  Bulk import workflow                Implemented

  OWL dashboard                       Implemented

  Scheduled alerts                    Implemented

  Unit/integration test files         Present

  Production deployment configuration Needs infrastructure setup

  Docker/Compose production stack     Not established by repository
documentation

  100--200 user load test             Not demonstrated

  Disaster recovery test              Not demonstrated

  High availability                   Not demonstrated
Production security audit           Not demonstrated
The repository documentation indicates that runtime installation against
a live Odoo database has not been performed as part of the archive
build. This does not mean the software is unsuitable for production. It
means staging installation, security testing, backup restoration and
load testing should be completed before institutional data is placed
into production.
18. Final server procurement specification
The following specification can be sent to a hosting provider or
infrastructure administrator.
FedEx-IIT production server
  Category            Specification
  Compute             8 dedicated or guaranteed vCPU
Memory              16 GB RAM
Storage             250 GB NVMe SSD
Network             1 Gbps interface preferred
Operating system    Ubuntu Server 24.04 LTS, 64-bit
Application         Odoo 18 Community
Runtime             Python 3.12
Database            PostgreSQL 16
Reverse proxy       Nginx
Initial workers     6 HTTP + 2 cron
Public access       HTTPS
Internal services   Odoo and PostgreSQL ports private
Backups             Daily, encrypted, off-site
Monitoring          Continuous infrastructure and application monitoring
Testing             Staging, recovery and load testing before launch

Target deployment: 100--200 registered users, with approximately
25--50 active concurrent users as an initial planning assumption.
19. Hosting providers to evaluate
These are providers to compare, not confirmed available instances or
live quotations.
- Hetzner Cloud --- cloud servers.
- DigitalOcean ---
  Droplet pricing.
- AWS EC2 --- compute pricing.
- Google Cloud Compute
  Engine --- compute
  pricing.
Compare actual CPU performance, NVMe IOPS, backup pricing, bandwidth,
region, support and recovery options rather than choosing based on
advertised RAM alone.
20. Decisions required to finalize the deployment
The 8-vCPU / 16-GB specification is the recommended starting point.
21. Final recommendation
Start with a properly configured 8-vCPU, 16-GB RAM production
server, external backups and a separate staging environment.

Before increasing capacity:
1. Optimize the import engine.
2. Optimize document checklist synchronization.
3. Review daily cron performance.
4. Benchmark dashboard and global-search queries.
5. Verify role-based and centre-based access.
6. Test backup restoration.
7. Run realistic concurrent-user load tests.
This provides a cost-conscious and defensible starting architecture for
the FedEx-IIT application. Scale vertically or separate the application
and database services when real workload measurements justify it.
References
- FedEx-IIT GitHub
  repository
- Odoo 18 deployment
  documentation
- PostgreSQL documentation
- Nginx documentation
- Let's Encrypt
- Locust documentation
- Prometheus documentation
- Grafana documentation
