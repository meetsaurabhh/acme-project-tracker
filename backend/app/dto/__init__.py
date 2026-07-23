"""Data Transfer Objects.

These define the contract between the outside world and the service layer.
They are deliberately separate from the ORM models: the database schema can
change without breaking the API, and the API can hide fields the database
holds (a password hash, for example).
"""
