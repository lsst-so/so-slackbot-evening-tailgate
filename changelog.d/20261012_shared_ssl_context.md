### Bug fixes

- The bot now shares one SSL context between the Slack Web API client and every Socket Mode connection, instead of creating a new one (and reloading the CA bundle) on each reconnect and API call. In a 27 h soak test this cut memory growth by about 75% and removed the ~0.9 MiB steps at reconnects (RSO-1006).
