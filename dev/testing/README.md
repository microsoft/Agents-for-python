## Testing

This folder contains three test-related directories:

`cross-sdk-tests`: End-to-end tests across all SDKs (Python, JavaScript, .NET). This is a work in progress.

`microsoft-agents-testing`: This is the testing framework used to facilitate testing agents. This is only for internal development purposes.

`python-sdk-tests`: These are integration tests related to the Python SDK. These are an extension of the Python SDK's unit tests. These tests are more specific that the ones in `cross-sdk-tests` because they look into the internals of Python SDK components for the running agents while the other test suite communicates purely over HTTP/HTTPS.

## Running tests and installation

The instructions to install the `microsoft-agents-testing` library are specificed in `microsoft-agents-testing/README.md`. To run the `python-sdk-tests`, `cd` into that directory and run `pytest` via Powershell. `cross-sdk-tests` still does not have an entry point for testing.