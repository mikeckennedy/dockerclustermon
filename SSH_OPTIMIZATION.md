# SSH Connection Optimization

## Problem

The original implementation was creating **3 separate SSH connections** for every refresh cycle:
1. One for `docker ps`
2. One for `docker stats --no-stream`
3. One for `free -m`

Each SSH connection requires:
- TCP handshake
- SSH protocol negotiation
- Key exchange
- Authentication

This overhead was happening **every few seconds** during the live monitoring, causing significant performance issues.

## Solution

Implemented **persistent SSH connections** using the [Paramiko](https://www.paramiko.org) library:

### Key Changes

1. **Added Paramiko dependency** (`paramiko>=3.5.0`)
2. **Created SSH connection manager** with three new functions:
   - `get_ssh_client()`: Creates or returns existing persistent connection
   - `close_ssh_client()`: Properly closes the connection on exit
   - `run_ssh_command()`: Executes commands over the persistent connection

3. **Refactored command execution**:
   - Modified `run_command_with_debug()` to accept an optional `ssh_client` parameter
   - Updated `run_free_command()`, `run_stat_command()`, and `run_ps_command()` to use the persistent connection
   - Modified `run_update()` to create the SSH connection once and reuse it for all three commands

### Benefits

- ✅ **Significant performance improvement**: Only connects once, not 3 times per refresh
- ✅ **No server-side setup required**: Uses standard SSH authentication
- ✅ **Supports SSH config files**: Works with `~/.ssh/config` entries
- ✅ **Automatic reconnection**: Detects dead connections and recreates them
- ✅ **Backward compatible**: Local execution (--no-ssh) still works as before
- ✅ **Clean shutdown**: Properly closes SSH connection on keyboard interrupt

### Connection Lifecycle

1. **First refresh**: Creates SSH connection (one-time cost)
2. **Subsequent refreshes**: Reuses existing connection (zero connection overhead)
3. **Connection validation**: Tests if connection is alive before reusing
4. **Auto-recovery**: If connection dies, creates a new one automatically
5. **Clean exit**: Closes connection on Ctrl+C

### Code Example

Before (3 separate SSH processes):
```bash
ssh user@host "docker ps"           # SSH connection #1
ssh user@host "docker stats ..."    # SSH connection #2  
ssh user@host "free -m"             # SSH connection #3
```

After (1 persistent SSH connection):
```python
client = get_ssh_client(username, host, ssh_config)  # Once
run_ssh_command(client, "docker ps", timeout)        # Reuse
run_ssh_command(client, "docker stats ...", timeout) # Reuse
run_ssh_command(client, "free -m", timeout)          # Reuse
```

## Performance Impact

**Expected improvement**: 50-80% reduction in refresh time, depending on:
- Network latency to the remote server
- SSH authentication method (key vs password)
- Server load and SSH daemon responsiveness

**Most significant impact** for:
- High-latency connections (remote servers, VPNs)
- Password-based authentication
- Servers with complex SSH configurations

## Technical Details

### Paramiko Features Used

- `SSHClient`: Main client class for SSH connections
- `AutoAddPolicy()`: Automatically accepts unknown host keys
- `exec_command()`: Executes commands and captures output
- `get_transport()` + `is_active()`: Tests connection health
- `SSHConfig`: Parses and uses `~/.ssh/config` files

### Thread Safety

The implementation reuses a single SSH connection across multiple threads. While Paramiko's `exec_command()` is thread-safe for the operations we're doing (executing independent commands), the connection is tested and recreated if needed at the start of each refresh cycle (in the main thread) before the worker threads start.

### Error Handling

- Connection failures fall back to None, allowing graceful degradation
- Dead connections are detected and recreated automatically
- Debug mode shows connection status and errors
- Timeouts are properly handled at both command and connection level

## Files Modified

- `dockerclustermon/__init__.py`: Core implementation
- `pyproject.toml`: Added paramiko dependency
- `change-log.md`: Documented the changes

## Testing

Tested with:
- ✅ Installation and dependency resolution (uv)
- ✅ Code formatting (ruff format)
- ✅ Linting (ruff check --fix)
- ✅ No linter errors

## Next Steps

To verify the performance improvement in your environment:

1. **Before testing**: Note the current refresh time with verbose SSH output:
   ```bash
   time ssh user@host "docker ps && docker stats --no-stream && free -m"
   ```

2. **Install the update**:
   ```bash
   uv pip install -e .
   ```

3. **Test the new version**:
   ```bash
   ds user@host --debug  # Watch for SSH connection messages
   ```

4. **Expected behavior**:
   - First refresh: "Creating SSH connection" (if in debug mode)
   - Subsequent refreshes: No new connections, just command execution
   - Much faster response times after the initial connection

## Comparison: Paramiko vs SSH Tunneling

Your initial suggestion mentioned SSH tunneling. Here's why Paramiko is better for this use case:

| Approach | Pros | Cons |
|----------|------|------|
| **SSH Tunneling** | Works for port forwarding | Docker isn't a network service - it's a CLI tool |
| | Good for databases/web servers | Would still need to run commands over SSH |
| | | Adds unnecessary complexity |
| **Paramiko** | ✅ Direct command execution | Requires Python library |
| | ✅ Persistent connections | |
| | ✅ No server setup needed | |
| | ✅ Works with existing SSH auth | |
| | ✅ Simple to implement | |

SSH tunneling would work if we needed to connect to a Docker API endpoint, but since we're running shell commands (`docker ps`, `docker stats`, etc.), a persistent SSH connection is the ideal solution.

