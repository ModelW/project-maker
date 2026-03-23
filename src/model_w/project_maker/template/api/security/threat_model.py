from pytm import TM, Actor, Boundary, Dataflow, Process, Datastore, ExternalEntity


tm = TM("Model W Django + SvelteKit Platform")
tm.description = """
Threat model for Model W projects.

Architecture:

Browser -> SvelteKit -> Django API/Wagtail
Workers -> background jobs
PostgreSQL + Redis
DigitalOcean Spaces storage
Sentry observability
Kerfu Foo deployment system
GitHub source control
"""

tm.assumptions = [
    "All external communication uses HTTPS",
    "Session authentication implemented using Django session cookies",
    "CSRF protection enabled via Django middleware",
    "Redis and PostgreSQL accessible only within private network",
    "DigitalOcean App Platform provides network isolation",
    "Public object storage used only for non-sensitive media assets",
    "Kerfu Foo manages deployment and secrets",
]


# Boundaries
internet = Boundary("Public Internet")
edge = Boundary("Edge Network / CDN / Load Balancer")
application = Boundary("Application Runtime (DigitalOcean App Platform)")
internal_services = Boundary("Internal Data Services")
external_services = Boundary("External SaaS Services")
administration = Boundary("Administrative Systems")
supply_chain = Boundary("Software Supply Chain")


# Actors
User = Actor("Public User")
Editor = Actor("CMS Editor")
Developer = Actor("Developer")
PlatformAdmin = Actor("Platform Administrator")


# Processes
Browser = Process("User Browser")
Browser.inBoundary = internet

Frontend = Process("SvelteKit Frontend")
Frontend.inBoundary = application

Backend = Process("Django API")
Backend.inBoundary = application

CMS = Process("Wagtail Admin")
CMS.inBoundary = application

Worker = Process("Background Worker (Procrastinate)")
Worker.inBoundary = application


# Datastores
Postgres = Datastore("PostgreSQL Database")
Postgres.inBoundary = internal_services

Redis = Datastore("Redis Cache / Channels")
Redis.inBoundary = internal_services

Spaces = Datastore("DigitalOcean Spaces Object Storage")
Spaces.inBoundary = external_services


# External Entities
Sentry = ExternalEntity("Sentry Monitoring")
Sentry.inBoundary = external_services

Kerfu = ExternalEntity("Kerfu Foo Deployment Platform")
Kerfu.inBoundary = administration

GitHub = ExternalEntity("GitHub Source Control")
GitHub.inBoundary = supply_chain

CI = ExternalEntity("CI/CD Pipeline")
CI.inBoundary = supply_chain


# Dataflows
user_to_browser = Dataflow(User, Browser, "User interaction")

browser_to_frontend = Dataflow(Browser, Frontend, "HTTPS request for web pages")
browser_to_frontend.protocol = "HTTPS"
browser_to_frontend.dstPort = 443

browser_to_backend = Dataflow(Browser, Backend, "API request with session cookie")
browser_to_backend.protocol = "HTTPS"
browser_to_backend.dstPort = 443

editor_login = Dataflow(Editor, CMS, "CMS login and content editing")
editor_login.protocol = "HTTPS"
editor_login.dstPort = 443

cms_db = Dataflow(CMS, Postgres, "CMS content read/write")
cms_db.protocol = "PostgreSQL"
cms_db.dstPort = 5432

frontend_api = Dataflow(Frontend, Backend, "Internal API request via platform network")
frontend_api.protocol = "HTTP"
frontend_api.dstPort = 8000

backend_db = Dataflow(Backend, Postgres, "Application data queries")
backend_db.protocol = "PostgreSQL"
backend_db.dstPort = 5432

backend_cache = Dataflow(Backend, Redis, "Caching / channels / session storage")
backend_cache.protocol = "Redis"
backend_cache.dstPort = 6379

backend_storage = Dataflow(Backend, Spaces, "Media uploads and asset storage")
backend_storage.protocol = "HTTPS"
backend_storage.dstPort = 443

task_dispatch = Dataflow(Backend, Worker, "Background job dispatch")
task_dispatch.protocol = "Procrastinate"
task_dispatch.dstPort = 8000

worker_db = Dataflow(Worker, Postgres, "Background job queries")
worker_db.protocol = "PostgreSQL"
worker_db.dstPort = 5432

worker_storage = Dataflow(Worker, Spaces, "File processing or asset generation")
worker_storage.protocol = "HTTPS"
worker_storage.dstPort = 443

backend_errors = Dataflow(Backend, Sentry, "Application errors and traces")
backend_errors.protocol = "HTTPS"
backend_errors.dstPort = 443

frontend_errors = Dataflow(Frontend, Sentry, "Frontend error reporting")
frontend_errors.protocol = "HTTPS"
frontend_errors.dstPort = 443

healthcheck = Dataflow(Browser, Backend, "Public health endpoint")
healthcheck.protocol = "HTTPS"
healthcheck.dstPort = 443

admin_to_kerfu = Dataflow(PlatformAdmin, Kerfu, "Administrative access")
admin_to_kerfu.protocol = "HTTPS"
admin_to_kerfu.dstPort = 443

kerfu_deploy = Dataflow(Kerfu, Backend, "Deployments and environment configuration")
kerfu_deploy.protocol = "SSH"
kerfu_deploy.dstPort = 22

kerfu_worker = Dataflow(Kerfu, Worker, "Worker deployment control")
kerfu_worker.protocol = "SSH"
kerfu_worker.dstPort = 22

developer_commit = Dataflow(Developer, GitHub, "Source code push")
developer_commit.protocol = "Git/HTTPS"
developer_commit.dstPort = 443

ci_build = Dataflow(GitHub, CI, "Build trigger")
ci_build.protocol = "Webhook/HTTPS"
ci_build.dstPort = 443

ci_deploy = Dataflow(CI, Kerfu, "Deployment artifacts")
ci_deploy.protocol = "HTTPS"
ci_deploy.dstPort = 443


if __name__ == "__main__":
    tm.process()
