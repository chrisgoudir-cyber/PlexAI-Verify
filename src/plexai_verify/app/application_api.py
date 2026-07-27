"""Compatibility entry point used by the current Qt interface."""
from plexai_verify.core.api.application import ApplicationAPI
app_api = ApplicationAPI.create_default()
