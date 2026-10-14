#!/bin/bash
unset NO_PROXY no_proxy http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
A=docs/harness/invokes/by-task/hitl-resume-async/attachments
B=http://127.0.0.1:8050
for i in $(seq 1 60); do
  code=$(curl -s -m 2 -o /dev/null -w "%{http_code}" "$B/docs" 2>/dev/null)
  if [ "$code" = "200" ]; then echo "READY@${i}s"; break; fi
  sleep 1
done
curl -s -c "$A/tc8.jar" -X POST "$B/api/ops/auth/login" -H "Content-Type: application/json" \
  -d '{"username":"admin","invite_token":"F1hrikP_pEO7YvRAVS9yFhJoNEOhwlj5jgz-RRKhHKY"}' -o "$A/tc8_login.json" -w "HTTP=%{http_code}\n"
cat "$A/tc8_login.json"; echo
