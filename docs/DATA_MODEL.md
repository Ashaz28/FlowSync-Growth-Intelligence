# Data Model

`accounts` 1→many `users`  
`accounts` 1→many `subscriptions`  
`accounts` 1→many `support_tickets`  
`accounts` 1→many `customer_feedback`  
`users` 1→many `product_events`  
`users` 1→many `ai_usage`  
`users` 1→many `experiments`  

The common business-level key is `account_id`. `user_id` supports user-level product analysis. Integration usage appears in `product_events.integration_name` and can be joined conceptually to `integrations.integration_name`.
