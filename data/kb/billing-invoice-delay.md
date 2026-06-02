# Invoice Generation Delay

Invoices are generated in hourly batches. If delayed beyond 2 hours, check billing-worker queue depth and failed jobs. Re-run billing batch for affected accounts.
