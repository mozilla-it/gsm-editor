# gsm-editor
A script for editing Google Secret Manager Secrets in a manner consistent with our intended External Secrets usage

# Examples

### List the secret versions in the stage env
`./gsm.py list -p moz-fx-testapp1-nonprod -e stage`

### view the latest version of the stage secret [or version 5]
`./gsm.py view -p moz-fx-testapp1-nonprod -e stage [-v 5]`

### edit the latest version of the stage secret
`./gsm.py edit -p moz-fx-testapp1-nonprod -e stage`
