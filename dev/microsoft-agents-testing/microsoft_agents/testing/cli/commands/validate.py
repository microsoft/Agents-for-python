# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# """Validate command - checks that CLI configuration is complete."""

# import click

# from ..config import CLIConfig
# from ..core.output import Output

# @click.command()
# @click.pass_context
# def validate(ctx: click.Context) -> None:
#     """Validate configuration and environment setup.
    
#     Checks that all required configuration values are present
#     and properly formatted.
#     """
#     config: CLIConfig = ctx.obj["config"]
#     verbose: bool = ctx.obj.get("verbose", False)
#     out = Output(verbose=verbose)
    
#     out.header("Configuration Validation")
    
#     # Track validation results
#     checks: list[tuple[str, str, bool]] = []
    
#     # Check environment file
#     if config.env_path:
#         checks.append(("Environment file", config.env_path, True))
#     else:
#         checks.append(("Environment file", "Not found (using defaults)", False))
    
#     # Check authentication settings
#     if config.app_id:
#         masked_id = config.app_id[:8] + "..." if len(config.app_id) > 8 else "***"
#         checks.append(("App ID", masked_id, True))
#     else:
#         checks.append(("App ID", "Not configured", False))
    
#     if config.app_secret:
#         checks.append(("App Secret", "********", True))
#     else:
#         checks.append(("App Secret", "Not configured", False))
    
#     if config.tenant_id:
#         checks.append(("Tenant ID", config.tenant_id, True))
#     else:
#         checks.append(("Tenant ID", "Not configured", False))
    
#     # Check agent/service URLs
#     if config.agent_url:
#         checks.append(("Agent URL", config.agent_url, True))
#     else:
#         checks.append(("Agent URL", "Not configured", False))
    
#     if config.service_url:
#         checks.append(("Service URL", config.service_url, True))
#     else:
#         checks.append(("Service URL", "Not configured", False))
    
#     # Display results
#     all_valid = True
#     for name, value, is_valid in checks:
#         if is_valid:
#             out.success(f"{name}: {value}")
#         else:
#             out.warning(f"{name}: {value}")
#             all_valid = False
    
#     out.newline()
    
#     if all_valid:
#         out.success("All configuration checks passed!")
#     else:
#         out.warning("Some configuration values are missing.")
#         out.info("Set missing values in your .env file or environment variables.")
