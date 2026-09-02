# Upgrade policy

Import an exact upstream commit on a feature branch, verify its official and
sanitized tree identities, update every digest-pinned build input, build and inspect
the image in CI, and promote the same protected source through development, test,
staging, production, and main. Never build the production image on a server.
