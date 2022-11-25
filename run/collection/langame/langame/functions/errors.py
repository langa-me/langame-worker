
def init_errors(env: str = "development"):
    import sentry_sdk
    from sentry_sdk.integrations.gcp import GcpIntegration

    sentry_sdk.init(
        "https://89b0a4a5cf3747ff9989710804f50dbb@o404046.ingest.sentry.io/6346831",

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        environment=env,
        integrations=[GcpIntegration()],

    )

