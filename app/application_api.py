"""Compatibility entry point used by the current Qt interface."""
from core.api.application import ApplicationAPI
app_api = ApplicationAPI.create_default()
