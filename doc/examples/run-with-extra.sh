#!/bin/bash
# Example: Using DDNS with extra fields via environment variables
# 
# This example shows how to configure Cloudflare provider with extra fields
# to enable proxied status and add custom comments to DNS records.

# Standard DDNS configuration
export DDNS_DNS=cloudflare
export DDNS_ID=user@example.com
export DDNS_TOKEN=your_api_token_here
export DDNS_IPV4='["example.com", "www.example.com"]'
export DDNS_INDEX4='["default"]'
export DDNS_TTL=600

# Extra fields for Cloudflare provider
# These will be passed to the Cloudflare API
export DDNS_EXTRA_PROXIED=true              # Enable Cloudflare proxy (orange cloud)
export DDNS_EXTRA_COMMENT="Managed by DDNS - Auto-updated"  # Add comment to record
export DDNS_EXTRA_TAGS='["production", "ddns"]'  # Add tags to record

# Run DDNS
python3 run.py

# Alternative: Using CLI arguments instead
# python3 run.py \
#   --dns cloudflare \
#   --id user@example.com \
#   --token your_api_token_here \
#   --ipv4 example.com www.example.com \
#   --extra.proxied true \
#   --extra.comment "Managed by DDNS" \
#   --extra.tags '["production", "ddns"]'
