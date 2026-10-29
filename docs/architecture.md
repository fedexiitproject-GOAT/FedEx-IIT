# Architecture & Data Models

The **FedEx Data Repository** module is designed with a high-integrity relational model following Odoo enterprise patterns.

## Identity & Delegation Inheritance

Personal identities in FedEx Data Repository leverage Odoo's standard `res.partner` table via delegation inheritance (`_inherits`). This guarantees seamless interoperability with native contact books, messaging chatter, and mail tracking.

```mermaid
classDiagram
    class ResPartner {
        +Integer id
        +String name
        +String email
        +String phone
    }
    class FedexStudentProfile {
        +Many2one partner_id
        +String roll_number
        +String program
        +Float cgpa
        +Many2one centre_id
    }
    class FedexFacultyProfile {
        +Many2one partner_id
        +String employee_id
        +String department
        +Many2one centre_id
    }
    class FedexStaffProfile {
        +Many2one partner_id
        +String staff_code
        +String role
        +Many2one centre_id
    }

    ResPartner <|-- FedexStudentProfile : _inherits
    ResPartner <|-- FedexFacultyProfile : _inherits
    ResPartner <|-- FedexStaffProfile : _inherits
```

## Relational Model Architecture

```mermaid
erDiagram
    FEDEX_CENTRE ||--o{ FEDEX_PROJECT : hosts
    FEDEX_CENTRE ||--o{ FEDEX_STUDENT_PROFILE : enrols
    FEDEX_PROJECT ||--o{ FEDEX_PROJECT_MEMBER : includes
    RES_PARTNER ||--o{ FEDEX_PROJECT_MEMBER : acts_as
    FEDEX_PROJECT ||--o{ FEDEX_DOCUMENT_REQUIREMENT : defines
    FEDEX_PROJECT ||--o{ FEDEX_DOCUMENT : stores
    FEDEX_PROJECT ||--o{ FEDEX_MILESTONE : tracks
    FEDEX_DOCUMENT_REQUIREMENT ||--o| FEDEX_DOCUMENT : satisfied_by
```

## Core Models Reference

| Technical Name | Human Label | Purpose |
|---|---|---|
| `fedex.centre` | Centre | IIT Bombay FedEx ALFA & IIT Madras FedEx SMART centres |
| `fedex.project` | Project | Research project lifecycle (Draft, Approved, In Progress, Completed, Cancelled) |
| `fedex.project.member` | Project Member | Team members, interns, co-supervisors, with duration and certificate flags |
| `fedex.project.milestone` | Milestone | Project deliverable milestones with due dates and completion states |
| `fedex.document` | Document | Document repository items (Person, Project, or Engagement scope) |
| `fedex.document.requirement` | Requirement | Checklist requirements bound to projects/members |
| `fedex.alert.log` | Alert Log | Automated audit alerts triggered by scheduled cron jobs |
