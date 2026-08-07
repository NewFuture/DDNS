#!/bin/sh
# Verify that regex IP detection neither launches an intermediate shell nor
# leaves zombie processes when crond is the container's PID 1.

set -eu

TEST_ROOT=/tmp/ddns-zombie-test
TEST_BIN="$TEST_ROOT/bin"
PARENT_LOG="$TEST_ROOT/ip-parents"
READY_FILE="$TEST_ROOT/ready"

setup_container() {
    mkdir -p "$TEST_BIN"
    cat > "$TEST_BIN/ip" <<'EOF'
#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ "$1" != "address" ]; then
    echo "Unexpected ip arguments: $*" >&2
    exit 64
fi

cat "/proc/$PPID/comm" >> /tmp/ddns-zombie-test/ip-parents
cat <<'EOF_IP_OUTPUT'
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet6 2001:db8::42/64 scope global
EOF_IP_OUTPUT
EOF
    chmod 755 "$TEST_BIN/ip"
    : > "$PARENT_LOG"
    : > "$READY_FILE"
}

check_process_tree() {
    init_name=$(cat /proc/1/comm)
    if [ "$init_name" != "tini" ]; then
        echo "Expected tini as PID 1, got $init_name" >&2
        return 1
    fi

    crond_parent=$(ps -o pid,ppid,stat,comm | awk 'NR > 1 && $4 == "crond" { print $2; exit }')
    if [ "$crond_parent" != "1" ]; then
        echo "Expected crond to be a direct child of tini, got PPID ${crond_parent:-missing}" >&2
        return 1
    fi
}

check_container() {
    expected_runs=$1
    actual_runs=$(wc -l < "$PARENT_LOG")

    check_process_tree

    if [ "$actual_runs" -ne "$expected_runs" ]; then
        echo "Expected $expected_runs ip executions, got $actual_runs" >&2
        cat "$PARENT_LOG" >&2
        exit 1
    fi

    if grep -Eq "^(sh|ash|busybox)$" "$PARENT_LOG"; then
        echo "Regex IP detection launched ip through an intermediate shell" >&2
        cat "$PARENT_LOG" >&2
        exit 1
    fi

    zombies=$(ps -o pid,ppid,stat,comm | awk 'NR > 1 && $3 ~ /^Z/ { print }')
    if [ -n "$zombies" ]; then
        echo "Zombie processes found after regex IP detection:" >&2
        echo "$zombies" >&2
        exit 1
    fi

    echo "Regex IP detection completed $actual_runs runs without shell intermediates or zombies"
}

case "${1:-}" in
    --setup)
        setup_container
        exit 0
        ;;
    --check)
        check_container "$2"
        exit 0
        ;;
    --ready)
        test -f "$READY_FILE"
        check_process_tree
        exit 0
        ;;
esac

image=${1:?Usage: test-docker-zombies.sh IMAGE [PLATFORM]}
platform=${2:-linux/amd64}
runs=${DDNS_ZOMBIE_TEST_RUNS:-8}
script_dir=$(cd "$(dirname "$0")" && pwd)
container="ddns-zombie-test-$$"

cleanup() {
    docker rm -f "$container" >/dev/null 2>&1 || true
}
trap cleanup 0 1 2 15

expected_entrypoint='["/sbin/tini","--","/bin/entrypoint.sh"]'
actual_entrypoint=$(docker image inspect --format '{{json .Config.Entrypoint}}' "$image")
if [ "$actual_entrypoint" != "$expected_entrypoint" ]; then
    echo "Unexpected image entrypoint: $actual_entrypoint" >&2
    exit 1
fi

docker run --detach \
    --name "$container" \
    --platform "$platform" \
    --entrypoint /sbin/tini \
    --volume "$script_dir:/tests:ro" \
    "$image" \
    -- /bin/sh -c "/bin/sh /tests/test-docker-zombies.sh --setup; exec crond -f" >/dev/null

attempt=0
until docker exec "$container" /bin/sh /tests/test-docker-zombies.sh --ready 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
        echo "Timed out waiting for the zombie test container" >&2
        docker logs "$container" >&2
        exit 1
    fi
    sleep 1
done

test_path="$TEST_BIN:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
run=0
while [ "$run" -lt "$runs" ]; do
    output=$(docker exec --env "PATH=$test_path" "$container" \
        /bin/ddns \
        --dns=debug \
        '--index6=regex:2001:db8:.*' \
        --ipv6=zombie-test.example \
        --cache=false)
    if ! printf '%s\n' "$output" | grep -q '^\[IPv6\] 2001:db8::42$'; then
        echo "Regex IPv6 result did not reach the debug provider:" >&2
        echo "$output" >&2
        exit 1
    fi
    run=$((run + 1))
done

sleep 1
docker exec "$container" /bin/sh /tests/test-docker-zombies.sh --check "$runs"

docker stop --time 5 "$container" >/dev/null
exit_code=$(docker inspect --format '{{.State.ExitCode}}' "$container")
if [ "$exit_code" -eq 137 ]; then
    echo "Container required SIGKILL instead of a graceful Tini shutdown" >&2
    exit 1
fi
echo "Tini forwarded shutdown with container exit code $exit_code"
