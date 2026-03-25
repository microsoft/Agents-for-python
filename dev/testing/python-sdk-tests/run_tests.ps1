Get-ChildItem -Path tests -Filter test_*.py -Recurse | ForEach-Object {
    pytest $_.FullName
}